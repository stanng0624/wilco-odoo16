from odoo import models, fields, api, _

REPORT_DISPLAY_ZERO_FORMAT = [
    ('included', 'Included'),
    ('excluded', 'Excluded'), 
    ('hyphen', '-')
]

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Basic fields
    wilco_line_ref = fields.Char(string='Line reference')
    wilco_report_display_zero_format = fields.Selection(
        selection=REPORT_DISPLAY_ZERO_FORMAT, 
        string='Display Zero In Report',
        default='included'
    )

    # Cost and profit fields
    wilco_budget_cost_unit = fields.Monetary(
        string="Unit cost",
        store=True
    )
    wilco_amount_budget_cost_total = fields.Monetary(
        string="Sub-total cost",
        store=True,
        compute='_wilco_compute_amount_budget_cost_total'
    )
    wilco_gross_profit_percent = fields.Float(
        string="Estimated GP%",
        compute='_wilco_compute_gross_profit_percent'
    )

    # Override compute methods
    @api.depends('product_id')
    def _compute_name(self):
        skip_update_lines = self._get_skip_update_lines('wilco_sale_skip_update_name')
        return super(SaleOrderLine, self - skip_update_lines)._compute_name()

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        skip_update_lines = self._get_skip_update_lines('wilco_sale_skip_update_price_unit')
        return super(SaleOrderLine, self - skip_update_lines)._compute_price_unit()

    @api.depends('display_type', 'product_id', 'product_packaging_qty')
    def _compute_product_uom_qty(self):
        skip_update_lines = self._get_skip_update_lines('wilco_sale_skip_update_qty')
        return super(SaleOrderLine, self - skip_update_lines)._compute_product_uom_qty()

    @api.depends('product_id')
    def _compute_product_uom(self):
        skip_update_lines = self._get_skip_update_lines('wilco_sale_skip_update_product_uom')
        return super(SaleOrderLine, self - skip_update_lines)._compute_product_uom()

    def _get_skip_update_lines(self, skip_field):
        return self.filtered(lambda r: r._origin.id
                           and not r.display_type
                           and r.product_id[skip_field])

    # Cost calculation methods
    @api.onchange('wilco_budget_cost_unit')
    def onchange_wilco_budget_cost_unit(self):
        if self.product_uom_qty and self.wilco_budget_cost_unit:
            self.wilco_amount_budget_cost_total = self.product_uom_qty * self.wilco_budget_cost_unit

    @api.depends('product_uom_qty', 'wilco_budget_cost_unit')
    def _wilco_compute_amount_budget_cost_total(self):
        for line in self:
            line.wilco_amount_budget_cost_total = line.product_uom_qty * line.wilco_budget_cost_unit

    @api.depends('product_uom_qty', 'price_subtotal', 'wilco_budget_cost_unit')
    def _wilco_compute_gross_profit_percent(self):
        for line in self:
            if line.price_subtotal > 0:
                cost_total = line.product_uom_qty * line.wilco_budget_cost_unit
                line.wilco_gross_profit_percent = (line.price_subtotal - cost_total) / line.price_subtotal
            else:
                line.wilco_gross_profit_percent = 0.0

    # Invoice preparation methods
    def _prepare_invoice_line(self, **optional_values):
        values = super()._prepare_invoice_line(**optional_values)

        if (self.order_id.wilco_invoice_method == 'invoice_by_order'
                and not self.display_type and not self.is_downpayment):
            values = self._set_invoice_line_for_invoice_by_order(values)

        return values

    def _set_invoice_line_for_invoice_by_order(self, values):
        sale_order = self.order_id
        order_ref = sale_order.wilco_document_number or sale_order.name
        
        values.update({
            'name': _('Bill to Order: {}').format(order_ref),
            'quantity': 1,
            'discount': 0,
            'price_unit': sale_order.wilco_amount_invoice_remainder
        })

        if sale_order.analytic_account_id:
            analytic_account_id_str = str(sale_order.analytic_account_id.id)
            values['analytic_distribution'] = {analytic_account_id_str: 100}

        return values

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.order_id.wilco_project_id.analytic_account_id:
                line._wilco_set_analytic_distribution_from_project()
        return lines

    def _wilco_set_analytic_distribution_from_project(self):
        self.ensure_one()
        if self.display_type:
            return

        project = self.order_id.wilco_project_id
        if project.analytic_account_id:
            analytic_account_id_str = str(project.analytic_account_id.id)
            self.analytic_distribution = {analytic_account_id_str: 100}

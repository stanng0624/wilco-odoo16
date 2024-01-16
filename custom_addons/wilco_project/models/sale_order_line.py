from odoo import models, fields, api, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    wilco_line_ref = fields.Char(string='Line reference')
    wilco_budget_cost_unit = fields.Monetary(string="Unit cost", stored=True)
    wilco_amount_budget_cost_total = fields.Monetary(string="Sub-total cost", stored=True, compute='_wilco_compute_amount_budget_cost_total')
    wilco_gross_profit_percent = fields.Float(string="GP%", compute='_wilco_compute_gross_profit_percent')

    @api.onchange('wilco_budget_cost_unit')
    def onchange_wilco_budget_cost_unit(self):
        if self.product_uom_qty != 0 and self.wilco_budget_cost_unit != 0:
            self.wilco_amount_budget_cost_total = self.product_uom_qty * self.wilco_budget_cost_unit

    @api.depends('product_uom_qty', 'wilco_budget_cost_unit')
    def _wilco_compute_amount_budget_cost_total(self):
        """
        Compute the amounts of the budget cost amount.
        """
        for line in self:
            amount_budget_cost_total = line.product_uom_qty * line.wilco_budget_cost_unit
            line.wilco_amount_budget_cost_total = amount_budget_cost_total

    @api.depends('product_uom_qty', 'price_subtotal', 'wilco_budget_cost_unit')
    def _wilco_compute_gross_profit_percent(self):
        """
        Compute the amounts of the budget cost amount.
        """
        for line in self:
            if line.price_subtotal > 0:
                amount_budget_cost_total = line.product_uom_qty * line.wilco_budget_cost_unit
                line.wilco_gross_profit_percent = (line.price_subtotal - amount_budget_cost_total) / line.price_subtotal
            else:
                line.wilco_gross_profit_percent = 0.0

    def _prepare_invoice_line(self, **optional_values):

        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)

        if self.order_id.wilco_invoice_method == 'invoice_by_order' and not self.display_type and not self.is_downpayment:
            values = self._set_invoice_line_for_invoice_by_order(values)

        return values

    def _set_invoice_line_for_invoice_by_order(self, values):
        sale_order = self.order_id

        order_ref = sale_order.wilco_document_number if sale_order.wilco_document_number else sale_order.name
        values['name'] = _('Bill to Order: {}').format(order_ref)
        values['quantity'] = 1
        values['discount'] = 0
        values['price_unit'] = sale_order.wilco_amount_invoice_remainder

        analytic_account_id = sale_order.analytic_account_id.id
        if analytic_account_id:
            analytic_account_id_str = str(analytic_account_id)
            values['analytic_distribution'] = {analytic_account_id_str: 100}

        return values
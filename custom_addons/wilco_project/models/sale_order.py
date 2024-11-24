from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, html_keep_url, is_html_empty
from odoo.addons.wilco_project.utils.external_identifier_util import ExternalIdentifierUtil

INVOICE_METHOD = [
    ('invoice_by_line', 'Invoice By Order Line'),
    ('invoice_by_order', 'Invoice By Order Total')
]

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Basic fields
    validity_date = fields.Date(string="Valid date")
    wilco_order_header = fields.Text(string='Quotation/Order header')
    wilco_our_ref = fields.Char(string='Our reference') 
    wilco_contact_info = fields.Text(string='Contact information')
    wilco_remark = fields.Text(string='Additional remarks')

    # Revision tracking fields
    wilco_revision_no = fields.Integer(string='Revision no.', default=0)
    wilco_revision_date = fields.Date(string='Revision date')
    wilco_document_number = fields.Char(string='Document number', compute='_wilco_compute_document_name')

    # Project related fields
    wilco_project_id = fields.Many2one(
        comodel_name='project.project', 
        string='Project',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        tracking=True,
        index=True
    )
    wilco_project_stage_id = fields.Many2one(
        comodel_name='project.project.stage',
        string="Project Stage",
        compute='_wilco_compute_project_info'
    )
    wilco_project_last_update_status = fields.Char(
        string="Project Status",
        compute='_wilco_compute_project_info'
    )

    # Invoice related fields
    wilco_invoice_method = fields.Selection(
        selection=INVOICE_METHOD,
        string="Invoice Method", 
        default='invoice_by_order',
        store=True
    )

    # Financial fields
    wilco_amount_invoiced_total = fields.Monetary(
        string="Invoiced",
        compute='_wilco_compute_invoiced_amounts'
    )
    wilco_amount_invoice_remainder = fields.Monetary(
        string="Invoiced Remainder",
        compute='_wilco_compute_invoiced_amounts'
    )
    wilco_amount_downpayment = fields.Monetary(
        string="Down Payment",
        compute='_wilco_compute_downpayment'
    )
    wilco_amount_downpayment_deducted = fields.Monetary(
        string="Down Payment Deducted",
        compute='_wilco_compute_invoiced_amounts'
    )
    wilco_amount_settled_total = fields.Monetary(
        string="Amount Settled",
        compute='_wilco_compute_settle_amounts'
    )
    wilco_amount_residual_total = fields.Monetary(
        string="Amount Due",
        compute='_wilco_compute_settle_amounts'
    )
    wilco_amount_budget_cost_total = fields.Monetary(
        string="Budget cost",
        compute='_wilco_compute_budget_amounts'
    )
    wilco_gross_profit_percent = fields.Float(
        string="GP%",
        compute='_wilco_compute_budget_amounts'
    )

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
        Override read_group to calculate the sum of the non-stored fields that depend on the user context
        """
        res = super().read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                orderby=orderby, lazy=lazy)
        
        fields_to_compute = [
            'wilco_amount_invoiced_total',
            'wilco_amount_invoice_remainder', 
            'wilco_amount_downpayment',
            'wilco_amount_downpayment_deducted',
            'wilco_amount_settled_total',
            'wilco_amount_residual_total',
            'wilco_amount_budget_cost_total',
            'wilco_gross_profit_percent'
        ]

        for line in res:
            if '__domain' in line:
                orders = self.search(line['__domain'])
                
                for field in fields_to_compute:
                    if field in fields:
                        if field == 'wilco_gross_profit_percent':
                            amount_total = sum(orders.mapped('amount_total'))
                            if amount_total == 0:
                                line[field] = 0
                            else:
                                amount_budget_cost_total = sum(orders.mapped('wilco_amount_budget_cost_total'))
                                line[field] = (amount_total - amount_budget_cost_total) / amount_total
                        else:
                            line[field] = sum(orders.mapped(field))

        return res

    def _wilco_get_sale_order_option_ids_not_selected(self):
        return self.sale_order_option_ids.filtered(lambda r: not r.is_present)

    @api.depends('order_line.invoice_lines')
    def _wilco_compute_invoiced_amounts(self):
        for order in self:
            invoices = order.invoice_ids.filtered(
                lambda inv: inv.move_type in ('out_invoice') and not inv._is_downpayment()
            )
            
            down_payment_deducted_lines = invoices.line_ids.filtered(
                lambda line: line.quantity < 0 and line.is_downpayment
            )

            amount_downpayment_deducted = sum(down_payment_deducted_lines.mapped("price_unit"))
            amount_invoiced_total = sum(invoices.mapped("amount_total_signed")) + amount_downpayment_deducted
            amount_invoice_remainder = max(order.amount_total - amount_invoiced_total, 0)

            order.update({
                'wilco_amount_downpayment_deducted': amount_downpayment_deducted,
                'wilco_amount_invoiced_total': amount_invoiced_total,
                'wilco_amount_invoice_remainder': amount_invoice_remainder
            })

    def _wilco_compute_downpayment(self):
        for order in self:
            down_payment_lines = order.order_line.filtered(
                lambda line: (line.is_downpayment and 
                            not line.display_type and 
                            not line._get_downpayment_state())
            )
            order.wilco_amount_downpayment = sum(down_payment_lines.mapped("price_unit"))

    def _wilco_compute_settle_amounts(self):
        for order in self:
            invoices = order.invoice_ids.filtered(lambda inv: inv.move_type in ('out_invoice'))
            order.wilco_amount_settled_total = sum(invoices.mapped("wilco_amount_settled_total_signed"))
            order.wilco_amount_residual_total = sum(invoices.mapped("amount_residual_signed"))

    @api.depends('order_line')
    def _wilco_compute_budget_amounts(self):
        for order in self:
            order_lines = order.order_line.filtered(
                lambda line: not line.is_downpayment and not line.display_type
            )
            order.wilco_amount_budget_cost_total = sum(order_lines.mapped("wilco_amount_budget_cost_total"))
            
            if order.amount_total == 0:
                order.wilco_gross_profit_percent = 0
            else:
                order.wilco_gross_profit_percent = (
                    order.amount_total - order.wilco_amount_budget_cost_total
                ) / order.amount_total

    @api.onchange('wilco_project_id')
    def onchange_wilco_project_id(self):
        self._wilco_set_project()
        for line in self.order_line:
            line._wilco_set_analytic_distribution_from_project()

    @api.onchange('wilco_revision_no')
    def onchange_wilco_revision_no(self):
        self.wilco_revision_date = fields.datetime.today() if self.wilco_revision_no > 0 else False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        
        for record in records:
            if ((record.wilco_project_id and not record.project_id) or
                (record.wilco_project_id and record.project_id != record.wilco_project_id) or
                (record.wilco_project_id.analytic_account_id and 
                 record.analytic_account_id != record.wilco_project_id.analytic_account_id)):
                record._wilco_set_project()

            if record.wilco_revision_no > 0 and not record.wilco_revision_date:
                record.wilco_revision_date = fields.datetime.today()

            if record.name:
                record.write_external_identifier(record.name)

        return records

    def write(self, values):
        result = super().write(values)
        
        for record in self:
            if 'wilco_project_id' in values:
                if ((record.wilco_project_id and not record.project_id) or
                    (record.wilco_project_id and record.project_id != record.wilco_project_id) or
                    (record.wilco_project_id.analytic_account_id and 
                     record.analytic_account_id != record.wilco_project_id.analytic_account_id)):
                    record._wilco_set_project()

            if 'wilco_revision_no' in values:
                if record.wilco_revision_no > 0 and not record.wilco_revision_date:
                    record.wilco_revision_date = fields.datetime.today()

            if values.get('name'):
                record.write_external_identifier(record.name)

        return result

    def _wilco_compute_document_name(self):
        for document in self:
            document.wilco_document_number = (
                f"{document.name}-R{document.wilco_revision_no}" 
                if document.wilco_revision_no > 0 
                else document.name
            )

    def _wilco_validate_sales_order_confirm(self):
        for order in self:
            if not order.order_line:
                raise UserError(_("No order line is confirmed. (Order: {})".format(order.name)))
            if not order.wilco_project_id:
                raise UserError(_("Project must be specified. (Order: {})".format(order.name)))

    def action_confirm(self):
        self._wilco_validate_sales_order_confirm()
        return super().action_confirm()

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        
        invoice_vals.update({
            'wilco_project_id': self.wilco_project_id.id,
            'wilco_our_ref': self.wilco_our_ref
        })

        use_invoice_terms = self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms')
        use_sale_terms = self.env['ir.config_parameter'].sudo().get_param('account.wilco_use_sale_terms')
        
        if use_sale_terms and use_invoice_terms:
            invoice_vals.pop('narration', None)

        return invoice_vals

    def _wilco_set_project(self):
        if self.wilco_project_id:
            self.update({
                'project_id': self.wilco_project_id,
                'wilco_our_ref': self.wilco_project_id.name,
                'analytic_account_id': self.wilco_project_id.analytic_account_id or False
            })

    def _get_invoiceable_lines(self, final=False):
        if self.wilco_invoice_method == 'invoice_by_order':
            return self._wilco_get_invoiceable_lines_for_invoice_by_order(final)
        return super()._get_invoiceable_lines(final)

    def _wilco_get_invoiceable_lines_for_invoice_by_order(self, final=False):
        down_payment_line_ids = []
        invoiceable_line_ids = []
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        is_invoice_line_added = False

        for line in self.order_line:
            if line.display_type == 'line_section':
                continue

            if line.is_downpayment:
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                        down_payment_line_ids.append(line.id)
                continue

            if line.display_type != 'line_note' and float_is_zero(line.product_uom_qty, precision_digits=precision):
                continue

            if line.product_uom_qty > 0 or (line.product_uom_qty < 0 and final):
                if not is_invoice_line_added:
                    invoiceable_line_ids.append(line.id)
                    is_invoice_line_added = True

        return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)

    @api.depends('state', 'order_line.invoice_status', 'order_line.invoice_lines.price_unit')
    def _compute_invoice_status(self):
        super()._compute_invoice_status()
        for order in self:
            order._wilco_update_invoice_status()

    def _wilco_update_invoice_status(self):
        self.ensure_one()

        if self.wilco_invoice_method == 'invoice_by_order':
            unconfirmed_orders = self.filtered(lambda so: so.state not in ['sale', 'done'])
            unconfirmed_orders.invoice_status = 'no'
            
            confirmed_orders = self - unconfirmed_orders
            if not confirmed_orders:
                return

            line_invoice_status_all = [
                (d['order_id'][0], d['invoice_status'])
                for d in self.env['sale.order.line'].read_group([
                    ('order_id', 'in', confirmed_orders.ids),
                    ('is_downpayment', '=', False),
                    ('display_type', '=', False),
                ],
                    ['order_id', 'invoice_status'],
                    ['order_id', 'invoice_status'], lazy=False)
            ]

            for order in confirmed_orders:
                line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
                
                if order.state not in ('sale', 'done'):
                    order.invoice_status = 'no'
                elif order.wilco_amount_invoice_remainder != 0:
                    order.invoice_status = 'to invoice'
                elif line_invoice_status and order.wilco_amount_invoice_remainder == 0:
                    order.invoice_status = 'invoiced'

    @api.depends('partner_id')
    def _compute_note(self):
        use_sale_terms = self.env['ir.config_parameter'].sudo().get_param('account.wilco_use_sale_terms')
        if not use_sale_terms:
            return super()._compute_note()

        for order in self:
            order = order.with_company(order.company_id)
            if order.terms_type == 'html' and self.env.company.wilco_sale_terms_html:
                baseurl = html_keep_url(order._get_note_url() + '/terms')
                order.note = _('Terms & Conditions: %s', baseurl)
            elif not is_html_empty(self.env.company.wilco_sale_terms):
                order.note = order.with_context(
                    lang=order.partner_id.lang
                ).env.company.wilco_sale_terms

    @api.depends('company_id', 'date_order')
    def _compute_validity_date(self):
        enabled_feature = bool(
            self.env['ir.config_parameter'].sudo().get_param('sale.use_quotation_validity_days')
        )
        if not enabled_feature:
            self.validity_date = False
            return

        super()._compute_validity_date()

        for order in self:
            if order.date_order:
                days = order.company_id.quotation_validity_days
                if days > 0:
                    order.validity_date = order.date_order + timedelta(days)

    def _wilco_compute_project_info(self):
        for record in self:
            record.wilco_project_stage_id = record.wilco_project_id.stage_id
            project_model = self.env['project.project']
            last_update_status_label = dict(
                project_model._fields['last_update_status'].selection
            ).get(record.wilco_project_id.last_update_status, False)
            record.wilco_project_last_update_status = last_update_status_label

    def wilco_action_view_analytic_lines(self):
        self.ensure_one()
        return {
            'res_model': 'account.analytic.line',
            'type': 'ir.actions.act_window',
            'name': _("Analytic Items"),
            'domain': [('account_id', '=', self.wilco_project_id.analytic_account_id.id)],
            'views': [
                (self.env.ref('analytic.view_account_analytic_line_tree').id, 'list'),
                (self.env.ref('analytic.view_account_analytic_line_form').id, 'form'),
                (self.env.ref('analytic.view_account_analytic_line_graph').id, 'graph'),
                (self.env.ref('analytic.view_account_analytic_line_pivot').id, 'pivot')
            ],
            'view_mode': 'tree,form,graph,pivot',
            'context': {
                'search_default_partner': 1,
                'default_account_id': self.wilco_project_id.analytic_account_id.id
            }
        }

    def write_external_identifier(self, name):
        return ExternalIdentifierUtil.write_external_identifier(
            self.env,
            self._name,
            self.id,
            name
        )
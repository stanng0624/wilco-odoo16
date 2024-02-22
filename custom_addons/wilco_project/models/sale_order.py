from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, html_keep_url, is_html_empty


INVOICE_METHOD = [
    ('invoice_by_line', 'Invoice By Order Line'),
    ('invoice_by_order', 'Invoice By Order Total')
]

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    validity_date = fields.Date(string="Valid date")

    wilco_order_header = fields.Text(string='Quotation/Order header')
    wilco_our_ref = fields.Char(string='Our reference')
    wilco_contact_info = fields.Text(string='Contact information')
    wilco_revision_no = fields.Integer(string='Revision no.', default=0)
    wilco_revision_date = fields.Date(string='Revision date')
    wilco_document_number = fields.Char(string='Document number', compute='_wilco_compute_document_name')
    wilco_remark = fields.Text(string='Additional remarks')
    wilco_project_id = fields.Many2one(
        'project.project', 'Project', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        index=True)
    wilco_invoice_method = fields.Selection(
        selection=INVOICE_METHOD,
        string="Invoice Mehtod",
        default='invoice_by_order',
        store=True)

    wilco_amount_invoiced_total = fields.Monetary(string="Invoiced", compute='_wilco_compute_invoiced_amounts')
    wilco_amount_invoice_remainder = fields.Monetary(string="Invoiced Remainder", compute='_wilco_compute_invoiced_amounts')
    wilco_amount_downpayment = fields.Monetary(string="Down Payment", compute='_wilco_compute_downpayment')
    wilco_amount_downpayment_deducted = fields.Monetary(string="Down Payment Deducted", compute='_wilco_compute_invoiced_amounts')
    wilco_amount_settled_total = fields.Monetary(string="Amount Settled", compute='_wilco_compute_settle_amounts')
    wilco_amount_residual_total = fields.Monetary(string="Amount Due", compute='_wilco_compute_settle_amounts')
    wilco_amount_budget_cost_total = fields.Monetary(string="Budget cost", compute='_wilco_compute_budget_amounts')
    wilco_gross_profit_percent = fields.Float(string="GP%", compute='_wilco_compute_budget_amounts')

    def _wilco_get_sale_order_option_ids_not_selected(self):
        sale_order_option_not_selected = self.sale_order_option_ids.filtered(lambda r: not r.is_present)
        return sale_order_option_not_selected

    @api.depends('order_line.invoice_lines')
    def _wilco_compute_invoiced_amounts(self):
        for order in self:
            invoices = order.invoice_ids.filtered(lambda invoice: invoice.move_type in ('out_invoice')
                                                                  and not invoice._is_downpayment())
            # refund_invoices = order.invoice_ids.filtered(lambda invoice: invoice.move_type in ('out_refund')
            #                                                       and not invoice._is_downpayment())
            down_payment_deducted_lines = invoices.line_ids.filtered(lambda line: line.quantity < 0 and line.is_downpayment)

            amount_downpayment_deducted = sum(down_payment_deducted_lines.mapped("price_unit"))
            amount_invoiced_total = sum(invoices.mapped("amount_total_signed")) + amount_downpayment_deducted
            amount_invoice_remainder = order.amount_total - amount_invoiced_total
            amount_invoice_remainder = amount_invoice_remainder if amount_invoice_remainder > 0 else 0

            order.wilco_amount_downpayment_deducted = amount_downpayment_deducted
            order.wilco_amount_invoiced_total = amount_invoiced_total
            order.wilco_amount_invoice_remainder = amount_invoice_remainder

    def _wilco_compute_downpayment(self):
        for order in self:
            down_payment_lines = order.order_line.filtered(lambda line:
                                                           line.is_downpayment
                                                           and not line.display_type
                                                           and not line._get_downpayment_state()
                                                           )
            order.wilco_amount_downpayment = sum(down_payment_lines.mapped("price_unit"))

    def _wilco_compute_settle_amounts(self):
        for order in self:
            #No refund amount
            invoices = order.invoice_ids.filtered(lambda invoice: invoice.move_type in ('out_invoice'))
            order.wilco_amount_settled_total = sum(invoices.mapped("wilco_amount_settled_total_signed"))
            order.wilco_amount_residual_total = sum(invoices.mapped("amount_residual_signed"))

    @api.depends('order_line')
    def _wilco_compute_budget_amounts(self):
        for order in self:
            order_lines = order.order_line.filtered(lambda line:
                                                    not line.is_downpayment
                                                    and not line.display_type
                                                    )
            order.wilco_amount_budget_cost_total = sum(order_lines.mapped("wilco_amount_budget_cost_total"))
            if order.amount_total == 0:
                order.wilco_gross_profit_percent = 0
            else:
                order.wilco_gross_profit_percent = (order.amount_total - order.wilco_amount_budget_cost_total) / order.amount_total

    @api.onchange('wilco_project_id')
    def onchange_wilco_project_id(self):
        self._wilco_set_project()

    @api.onchange('wilco_revision_no')
    def onchange_wilco_revision_no(self):
        if self.wilco_revision_no == 0:
            self.wilco_revision_date = ""
        else:
            self.wilco_revision_date = fields.datetime.today()

    @api.model_create_multi
    def create(self, vals_list):
        result = super(SaleOrder, self).create(vals_list)

        for order in result:
            if (order.wilco_project_id and not order.project_id) \
            or (order.wilco_project_id and order.project_id != order.wilco_project_id)\
            or (order.wilco_project_id.analytic_account_id and order.analytic_account_id != order.wilco_project_id.analytic_account_id):
                order._wilco_set_project()

            if order.wilco_revision_no > 0 and not order.wilco_revision_date:
                order.wilco_revision_date = fields.datetime.today()

            if order.name:
                order._wilco_write_external_identifier(order.name)

        return result

    def write(self, values):
        result = super(SaleOrder, self).write(values)

        for order in self:
            if 'wilco_project_id' in values:
                if (order.wilco_project_id and not order.project_id) \
                or (order.wilco_project_id and order.project_id != order.wilco_project_id)\
                or (order.wilco_project_id.analytic_account_id and order.analytic_account_id != order.wilco_project_id.analytic_account_id):
                    order._wilco_set_project()

            if 'wilco_revision_no' in values:
                if order.wilco_revision_no > 0 and not order.wilco_revision_date:
                    order.wilco_revision_date = fields.datetime.today()

            if 'name' in values:
                if order.name:
                    order._wilco_write_external_identifier(order.name)

        return result

    def _wilco_compute_document_name(self):
        for document in self:
            name = ""
            if document.wilco_revision_no > 0:
                name = "{}-R{}".format(document.name,document.wilco_revision_no)
            else:
                name = document.name
            document.wilco_document_number = name

    def _wilco_validate_sales_order_confirm(self):
        for order in self:
            if len(order.order_line) <= 0:
                raise UserError(_("No order line is confirmed. (Order: {})".format(order.name)))
            if not order.wilco_project_id:
                raise UserError(_("Project must be specified. (Order: {})".format(order.name)))

    def action_confirm(self):
        self._wilco_validate_sales_order_confirm()

        return super(SaleOrder, self).action_confirm()

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()

        invoice_vals['wilco_project_id'] = self.wilco_project_id.id
        invoice_vals['wilco_our_ref'] = self.wilco_our_ref

        use_invoice_terms = self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms')
        use_sale_terms = self.env['ir.config_parameter'].sudo().get_param('account.wilco_use_sale_terms')
        # Do not transfer terms and condition from SO to Invoice when enable both sales and invoice's terms & condition
        if use_sale_terms and use_invoice_terms:
            invoice_vals.pop('narration')

        return invoice_vals

    def _wilco_exist_external_identifier(
            self,
            # external_identifier_name: str,
            module = '__import__'):
        self.ensure_one()

        # external_identifier = self.env['ir.model.data'].search([
        #     ('name', '=', external_identifier_name),
        #     ('module', '=', module),
        #     ('model', '=', self._name),
        #     ('res_id', '!=', self.id),
        # ], limit=1)
        #
        # if external_identifier:
        #     return True

        external_identifier = self.env['ir.model.data'].sudo().search([
            ('module', '=', module),
            ('model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)

        if external_identifier:
            return True

        return False

    def _wilco_create_external_identifier(
            self,
            external_identifier_name: str,
            module = '__import__'):
        self.ensure_one()
        # Remove space, name is not allowed with space
        external_identifier_name = external_identifier_name.replace(" ","")
        self.env['ir.model.data'].sudo().create({
            'name': external_identifier_name,
            'module': module,
            'model': self._name,
            'res_id': self.id,
            'noupdate': False
        })

    def _wilco_update_external_identifier(
            self,
           external_identifier_name: str,
            module='__import__'):
        self.ensure_one()
        # Remove space, name is not allowed with space
        external_identifier_name = external_identifier_name.replace(" ","")

        # external_identifier = self.env['ir.model.data'].search([
        #     ('name', '=', external_identifier_name),
        #     ('module', '=', module),
        #     ('model', '=', self._name),
        # ], limit=1)
        #
        # if external_identifier and external_identifier.res_id != self.id:
        #     external_identifier.sudo().write({'res_id': self.id})
        #     return

        external_identifier = self.env['ir.model.data'].sudo().search([
            ('module', '=', module),
            ('model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)

        if external_identifier and external_identifier.name != external_identifier_name:
            external_identifier.sudo().write({'name': external_identifier_name})

    def _wilco_write_external_identifier(
            self,
            external_identifier_name: str,
            module='__import__',
            override_existing_id = True):
        self.ensure_one()
        # if override_existing_id and self._wilco_exist_external_identifier(external_identifier_name, module):
        if override_existing_id and self._wilco_exist_external_identifier(module):
            self._wilco_update_external_identifier(external_identifier_name, module)
        else:
            self._wilco_create_external_identifier(external_identifier_name, module)


    def _wilco_set_project(self):
        if self.wilco_project_id:
            self.project_id = self.wilco_project_id
            self.wilco_our_ref = self.wilco_project_id.name
            if self.wilco_project_id.analytic_account_id:
                self.analytic_account_id = self.wilco_project_id.analytic_account_id

    def _get_invoiceable_lines(self, final=False):
        result = super(SaleOrder, self)._get_invoiceable_lines(final)

        if self.wilco_invoice_method == 'invoice_by_order':
            result = self._wilco_get_invoiceable_lines_for_invoice_by_order(final)

        return result


    def _wilco_get_invoiceable_lines_for_invoice_by_order(self, final=False):
        down_payment_line_ids = []
        invoiceable_line_ids = []
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        is_invoice_line_added = False

        for line in self.order_line:
            if line.display_type == 'line_section':
                continue
            if line.is_downpayment:
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
            if line.display_type != 'line_note' and float_is_zero(line.product_uom_qty, precision_digits=precision):
                continue
            if line.product_uom_qty > 0 or (line.product_uom_qty < 0 and final):
                if not is_invoice_line_added:
                    invoiceable_line_ids.append(line.id)
                    is_invoice_line_added = True

        return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)

    # @api.depends('state', 'order_line.invoice_status', 'order_line.invoice_lines')
    @api.depends('state', 'order_line.invoice_status', 'order_line.invoice_lines.price_unit')
    def _compute_invoice_status(self):

        super(SaleOrder, self)._compute_invoice_status()

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
                    ['order_id', 'invoice_status'], lazy=False)]
            for order in confirmed_orders:
                line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
                if order.state not in ('sale', 'done'):
                    order.invoice_status = 'no'
                elif order.wilco_amount_invoice_remainder != 0:
                    order.invoice_status = 'to invoice'
                elif line_invoice_status and order.wilco_amount_invoice_remainder == 0:
                    order.invoice_status = 'invoiced'
                # Not use for upselling and To-do if needed
                # elif line_invoice_status and all(invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                #      order.invoice_status = 'upselling'
                # else:
                #     order.invoice_status = 'no'

    @api.depends('partner_id')
    def _compute_note(self):
        use_sale_terms = self.env['ir.config_parameter'].sudo().get_param('account.wilco_use_sale_terms')
        if not use_sale_terms:
            return super()._compute_note() #Use standard invoice/order/quotations terms & condition if not setup
        for order in self:
            order = order.with_company(order.company_id)
            if order.terms_type == 'html' and self.env.company.wilco_sale_terms_html:
                baseurl = html_keep_url(order._get_note_url() + '/terms')
                context = {'lang': order.partner_id.lang or self.env.user.lang}
                order.note = _('Terms & Conditions: %s', baseurl)
                del context
            elif not is_html_empty(self.env.company.wilco_sale_terms):
                order.note = order.with_context(lang=order.partner_id.lang).env.company.wilco_sale_terms

    @api.depends('company_id','date_order')
    def _compute_validity_date(self):
        enabled_feature = bool(self.env['ir.config_parameter'].sudo().get_param('sale.use_quotation_validity_days'))
        if not enabled_feature:
            self.validity_date = False
            return

        super()._compute_validity_date()

        for order in self:
            if order.date_order:
                days = order.company_id.quotation_validity_days
                if days > 0:
                    order.validity_date = order.date_order + timedelta(days)
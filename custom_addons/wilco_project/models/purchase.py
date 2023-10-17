from odoo import models, fields, api, _
from odoo.exceptions import UserError

READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    wilco_order_header = fields.Text(string='Quotation/Order header')
    wilco_our_ref = fields.Char(string='Our reference')
    wilco_contact_info = fields.Text(string='Contact information')
    wilco_revision_no = fields.Integer(string='Revision no.', default=0)
    wilco_revision_date = fields.Date(string='Revision date')
    wilco_document_number = fields.Char(string='Document number', compute='_wilco_compute_document_name')
    wilco_remark = fields.Text(string='Additional remarks')
    wilco_project_id = fields.Many2one(
        'project.project', 'Project', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    wilco_analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string="Analytic Account",
        copy=False, check_company=True,  # Unrequired company
        states=READONLY_STATES,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.onchange('wilco_project_id')
    def onchange_wilco_project_id(self):
        if self.wilco_project_id:
            self.wilco_our_ref = self.wilco_project_id.name
            self.wilco_analytic_account_id = self.wilco_project_id.analytic_account_id

    @api.onchange('wilco_revision_no')
    def onchange_wilco_revision_no(self):
        if self.wilco_revision_no == 0:
            self.wilco_revision_date = ""
        else:
            self.wilco_revision_date = fields.datetime.today()

    def _wilco_compute_document_name(self):
        for document in self:
            name = ""
            if document.wilco_revision_no > 0:
                name = f"{document.name}-R{document.wilco_revision_no}"
            else:
                name = document.name
            document.wilco_document_number = name

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()

        invoice_vals['wilco_project_id'] = self.wilco_project_id.id
        invoice_vals['wilco_our_ref'] = self.wilco_our_ref

        return invoice_vals

    def _wilco_validate_purchase_order_confirm(self):
        for order in self:
            if len(order.order_line) <= 0:
                raise UserError(_(f"No order line is confirmed. (Order: {order.name})"))
            if not order.wilco_project_id:
                raise UserError(_(f"Project must be specified. (Order: {order.name})"))

    def button_confirm(self):
        self._wilco_validate_purchase_order_confirm()

        super(PurchaseOrder, self).button_confirm()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)

        analytic_account_id = self.order_id.wilco_analytic_account_id.id
        if analytic_account_id and not self.display_type:
            analytic_account_id = str(analytic_account_id)
            if 'analytic_distribution' in res:
                res['analytic_distribution'][analytic_account_id] = res['analytic_distribution'].get(analytic_account_id, 0) + 100
            else:
                res['analytic_distribution'] = {analytic_account_id: 100}

        return res

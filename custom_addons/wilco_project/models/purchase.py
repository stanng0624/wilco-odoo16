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
        self._wilco_set_project()

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
                name = "{}-R{}".format(document.name, document.wilco_revision_no)
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
                raise UserError(_("No order line is confirmed. (Order: {})".format(order.name)))
            if not order.wilco_project_id:
                raise UserError(_("Project must be specified. (Order: {})".format(order.name)))

    def button_confirm(self):
        self._wilco_validate_purchase_order_confirm()

        super(PurchaseOrder, self).button_confirm()

    @api.model_create_multi
    def create(self, vals_list):
        result = super(PurchaseOrder, self).create(vals_list)

        for order in result:
            if order.wilco_project_id.analytic_account_id and order.wilco_analytic_account_id != order.wilco_project_id.analytic_account_id:
                order._wilco_set_project()

            if order.wilco_revision_no > 0 and not order.wilco_revision_date:
                order.wilco_revision_date = fields.datetime.today()

            if order.name:
                order._wilco_write_external_identifier(order.name)

        return result

    def write(self, values):
        result = super(PurchaseOrder, self).write(values)

        for order in self:
            if 'wilco_revision_no' in values:
                if order.wilco_revision_no > 0 and not order.wilco_revision_date:
                    order.wilco_revision_date = fields.datetime.today()

            if 'name' in values:
                if order.name:
                    order._wilco_write_external_identifier(order.name)

        return result

    def _wilco_exist_external_identifier(self, module='__import__'):
        self.ensure_one()
        external_identifier = self.env['ir.model.data'].search([
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
            module='__import__'):
        self.ensure_one()
        # Remove space, name is not allowed with space
        external_identifier_name = external_identifier_name.replace(" ", "")
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
        external_identifier_name = external_identifier_name.replace(" ", "")
        external_identifier = self.env['ir.model.data'].search([
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
            override_existing_id=True):
        self.ensure_one()
        if override_existing_id and self._wilco_exist_external_identifier(module):
            self._wilco_update_external_identifier(external_identifier_name, module)
        else:
            self._wilco_create_external_identifier(external_identifier_name, module)

    def _wilco_set_project(self):
        if self.wilco_project_id:
            self.wilco_our_ref = self.wilco_project_id.name
            if self.wilco_project_id.analytic_account_id:
                self.wilco_analytic_account_id = self.wilco_project_id.analytic_account_id


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    wilco_line_ref = fields.Char(string='Line reference')
    wilco_skip_update_name = fields.Boolean(string="Skip update name", compute="_wilco_compute_skip_update_name")

    def _wilco_compute_skip_update_name(self):
        for line in self:
            line.wilco_skip_update_name = line.product_id.wilco_purchase_skip_update_name

    def _get_product_purchase_description(self, product_lang):
        #Since their input of description is too long, the change of product to revise name is not necessary
        if self.name and self.wilco_skip_update_name:
            return self.name

        return super()._get_product_purchase_description(product_lang)

    def _prepare_account_move_line(self, move=False):
        result = super(PurchaseOrderLine, self)._prepare_account_move_line(move)

        analytic_account_id = self.order_id.wilco_analytic_account_id.id
        if analytic_account_id and not self.display_type:
            analytic_account_id = str(analytic_account_id)
            if 'analytic_distribution' in result:
                result['analytic_distribution'][analytic_account_id] = result['analytic_distribution'].get(analytic_account_id, 0) + 100
            else:
                result['analytic_distribution'] = {analytic_account_id: 100}

        return result

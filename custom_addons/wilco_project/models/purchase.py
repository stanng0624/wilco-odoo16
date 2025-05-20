from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.wilco_project.utils.external_identifier_util import ExternalIdentifierUtil

READONLY_STATES = {
    'purchase': [('readonly', True)],
    'done': [('readonly', True)], 
    'cancel': [('readonly', True)],
}

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Basic fields
    date_approve = fields.Datetime(readonly=0)
    wilco_order_header = fields.Text(string='Quotation/Order header')
    wilco_our_ref = fields.Char(string='Our reference') 
    wilco_contact_info = fields.Text(string='Contact information')
    wilco_remark = fields.Text(string='Additional remarks')

    # Revision fields
    wilco_revision_no = fields.Integer(string='Revision no.', default=0)
    wilco_revision_date = fields.Date(string='Revision date')
    wilco_document_number = fields.Char(string='Document number', compute='_wilco_compute_document_name')

    # Project related fields
    wilco_project_id = fields.Many2one(
        'project.project', 'Project', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        tracking=True,
        index=True)
    wilco_project_stage_id = fields.Many2one(
        comodel_name='project.project.stage',
        string="Project Stage", 
        compute='_wilco_compute_project_info')
    wilco_project_last_update_status = fields.Char(
        string="Project Status",
        compute='_wilco_compute_project_info')
    wilco_analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string="Analytic Account",
        copy=False, check_company=True,
        states=READONLY_STATES,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    # Project related methods
    @api.onchange('wilco_project_id')
    def onchange_wilco_project_id(self):
        self._wilco_set_project()

    def _wilco_set_project(self):
        if self.wilco_project_id:
            self.wilco_our_ref = self.wilco_project_id.name
            if self.wilco_project_id.analytic_account_id:
                self.wilco_analytic_account_id = self.wilco_project_id.analytic_account_id

    def _wilco_compute_project_info(self):
        for record in self:
            record.wilco_project_stage_id = record.wilco_project_id.stage_id
            project_model = self.env['project.project']
            last_update_status_label = dict(project_model._fields['last_update_status'].selection).get(
                record.wilco_project_id.last_update_status, False)
            record.wilco_project_last_update_status = last_update_status_label

    # Revision related methods
    @api.onchange('wilco_revision_no')
    def onchange_wilco_revision_no(self):
        if self.wilco_revision_no == 0:
            self.wilco_revision_date = ""
        else:
            self.wilco_revision_date = fields.datetime.today()

    def _wilco_compute_document_name(self):
        for document in self:
            name = document.name
            if document.wilco_revision_no > 0:
                name = f"{document.name}-R{document.wilco_revision_no}"
            document.wilco_document_number = name

    # Invoice related methods
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'wilco_project_id': self.wilco_project_id.id,
            'wilco_our_ref': self.wilco_our_ref
        })
        return invoice_vals

    # Validation methods
    def _wilco_validate_purchase_order_confirm(self):
        for order in self:
            if len(order.order_line) <= 0:
                raise UserError(_("No order line is confirmed. (Order: {})".format(order.name)))
            if not order.wilco_project_id:
                raise UserError(_("Project must be specified. (Order: {})".format(order.name)))

    def button_confirm(self):
        self._wilco_validate_purchase_order_confirm()
        super().button_confirm()

    # CRUD methods
    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)

        for order in result:
            if (order.wilco_project_id.analytic_account_id and 
                order.wilco_analytic_account_id != order.wilco_project_id.analytic_account_id):
                order._wilco_set_project()

            if order.wilco_revision_no > 0 and not order.wilco_revision_date:
                order.wilco_revision_date = fields.datetime.today()

            if order.name:
                order.write_external_identifier(order.name)

        return result

    def write(self, vals):
        result = super().write(vals)

        for order in self:
            if 'wilco_revision_no' in vals:
                if order.wilco_revision_no > 0 and not order.wilco_revision_date:
                    order.wilco_revision_date = fields.datetime.today()

            if 'name' in vals and order.name:
                order.write_external_identifier(order.name)

        return result

    # Utility methods
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

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    wilco_line_ref = fields.Char(string='Line reference')

    @api.depends('product_qty', 'product_uom', 'company_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        skip_update_lines = self._get_skip_update_lines('wilco_purchase_skip_update_price_unit')
        return super(PurchaseOrderLine, self - skip_update_lines)._compute_price_unit_and_date_planned_and_name()

    @api.depends('product_packaging_qty')
    def _compute_product_qty(self):
        skip_update_lines = self._get_skip_update_lines('wilco_purchase_skip_update_qty')
        return super(PurchaseOrderLine, self - skip_update_lines)._compute_product_qty()

    @api.depends('product_uom', 'product_qty', 'product_id.uom_id')
    def _compute_product_uom_qty(self):
        skip_update_lines = self._get_skip_update_lines('wilco_purchase_skip_update_qty')
        return super(PurchaseOrderLine, self - skip_update_lines)._compute_product_uom_qty()

    def _get_skip_update_lines(self, skip_field):
        return self.filtered(lambda r: r._origin.id
                           and r.display_type not in ('line_section', 'line_note')
                           and r.product_id[skip_field])

    def _get_product_purchase_description(self, product_lang):
        if self._origin.id and self.name and self.product_id.wilco_purchase_skip_update_name:
            return self.name
        return super()._get_product_purchase_description(product_lang)

    def _prepare_account_move_line(self, move=False):
        result = super()._prepare_account_move_line(move)

        analytic_account_id = self.order_id.wilco_analytic_account_id.id
        if analytic_account_id and not self.display_type:
            analytic_account_id = str(analytic_account_id)
            if 'analytic_distribution' in result:
                result['analytic_distribution'][analytic_account_id] = result['analytic_distribution'].get(analytic_account_id, 0) + 100
            else:
                result['analytic_distribution'] = {analytic_account_id: 100}

        return result

    def _product_id_change(self):
        super()._product_id_change()
        for line in self:
            line._reverse_origin_info_for_skip_update_purchase_info()

    @api.onchange('product_id')
    def onchange_product_id(self):
        super().onchange_product_id()
        self._reverse_origin_info_for_skip_update_purchase_info()

    def _reverse_origin_info_for_skip_update_purchase_info(self):
        self.ensure_one()

        if not self._origin.id or self.display_type in ('line_section', 'line_note'):
            return

        product = self.product_id
        if product.wilco_purchase_skip_update_product_uom and self.product_uom != self._origin.product_uom:
            self.product_uom = self._origin.product_uom

        if product.wilco_purchase_skip_update_qty:
            if self.product_qty != self._origin.product_qty:
                self.product_qty = self._origin.product_qty
            if self.product_uom_qty != self._origin.product_uom_qty:
                self.product_uom_qty = self._origin.product_uom_qty

        if product.wilco_purchase_skip_update_price_unit and self.price_unit != self._origin.price_unit:
            self.price_unit = self._origin.price_unit

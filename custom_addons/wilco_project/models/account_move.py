from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    wilco_our_ref = fields.Char(string='Our reference')
    wilco_contact_info = fields.Text(string='Contact information')
    wilco_revision_no = fields.Integer(string='Revision no.', default=0)
    wilco_revision_date = fields.Date(string='Revision date')
    wilco_document_number = fields.Char(string='Document number', compute='_wilco_compute_document_name')
    wilco_project_id = fields.Many2one(
        'project.project', 'Project', readonly=True,
        states={'draft': [('readonly', False)]})
    wilco_amount_settled_total = fields.Monetary(string="Amount Settled", compute='_wilco_compute_settled_amounts')
    wilco_amount_settled_total_signed = fields.Monetary(string="Amount Settled in Currency", compute='_wilco_compute_settled_amounts')

    def _wilco_compute_settled_amounts(self):
        for order in self:
            order.wilco_amount_settled_total = order.amount_total - order.amount_residual
            order.wilco_amount_settled_total_signed = order.amount_total_signed - order.amount_residual_signed

    @api.onchange('wilco_revision_no')
    def onchange_wilco_revision_no(self):
        if self.wilco_revision_no == 0:
            self.wilco_revision_date = ""
        else:
            self.wilco_revision_date = fields.datetime.today()

    @api.onchange('wilco_project_id')
    def onchange_wilco_project_id(self):
        if self.wilco_project_id:
            self.wilco_our_ref = self.wilco_project_id.name


from odoo import models, fields, api, _
from odoo.tools import is_html_empty

class AccountMove(models.Model):
    _inherit = 'account.move'

    wilco_our_ref = fields.Char(string='Our reference')
    wilco_contact_info = fields.Text(string='Contact information')
    wilco_revision_no = fields.Integer(string='Revision no.', default=0)
    wilco_revision_date = fields.Date(string='Revision date')
    wilco_document_number = fields.Char(string='Document number', compute='_wilco_compute_document_name')

    wilco_project_id = fields.Many2one(
        comodel_name='project.project', string='Project', readonly=True,
        states={'draft': [('readonly', False)]},
        tracking=True,
        index=True)
    wilco_project_stage_id = fields.Many2one(
        comodel_name='project.project.stage',
        string="Project Stage",
        compute='_wilco_compute_project_info')
    wilco_project_last_update_status = fields.Char(
        string="Project Status",
        compute='_wilco_compute_project_info')

    wilco_amount_settled_total = fields.Monetary(string="Amount Settled", compute='_wilco_compute_settled_amounts')
    wilco_amount_settled_total_signed = fields.Monetary(string="Amount Settled in Currency", compute='_wilco_compute_settled_amounts')

    def _wilco_compute_project_info(self):
        for order in self:
            order.wilco_project_stage_id = order.wilco_project_id.stage_id
            order.wilco_project_last_update_status = order.wilco_project_id.last_update_status

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

    def _wilco_compute_document_name(self):
        for document in self:
            name = ""
            if document.wilco_revision_no > 0:
                name = "{}-R{}".format(document.name, document.wilco_revision_no)
            else:
                name = document.name
            document.wilco_document_number = name


    @api.onchange('wilco_project_id')
    def onchange_wilco_project_id(self):
        if self.wilco_project_id:
            self.wilco_our_ref = self.wilco_project_id.name
            # lines = self.line_ids.filtered(lambda r: r.display_type in ['payment_term','product'])
            lines = self.line_ids
            for line in lines:
                line._wilco_set_analytic_distribution_from_project()


    def _wilco_compute_project_info(self):
        for record in self:
            record.wilco_project_stage_id = record.wilco_project_id.stage_id
            project_model = self.env['project.project']
            last_update_status_label = dict(project_model._fields['last_update_status'].selection).get(record.wilco_project_id.last_update_status, False)
            record.wilco_project_last_update_status = last_update_status_label


    def wilco_action_view_analytic_lines(self):
        self.ensure_one()
        return {
            'res_model': 'account.analytic.line',
            'type': 'ir.actions.act_window',
            'name': _("Analytic Items"),
            'domain': [('account_id', '=', self.wilco_project_id.analytic_account_id.id)],
            'views': [(self.env.ref('analytic.view_account_analytic_line_tree').id, 'list'),
                      (self.env.ref('analytic.view_account_analytic_line_form').id, 'form'),
                      (self.env.ref('analytic.view_account_analytic_line_graph').id, 'graph'),
                      (self.env.ref('analytic.view_account_analytic_line_pivot').id, 'pivot')],
            'view_mode': 'tree,form,graph,pivot',
            # 'context': {'search_default_group_date': 1, 'default_account_id': self.wilco_project_id.analytic_account_id.id}
            'context': {'search_default_partner': 1, 'default_account_id': self.wilco_project_id.analytic_account_id.id}
        }
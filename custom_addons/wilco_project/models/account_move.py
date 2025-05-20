from odoo import models, fields, api, _
from odoo.tools import is_html_empty

class AccountMove(models.Model):
    _inherit = 'account.move'

    wilco_payment_dates = fields.Char(string='Payment Date(s)', compute='_compute_wilco_payment_dates', store=True, help="Dates of payments made against this invoice")
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
    wilco_amount_downpayment = fields.Monetary(
        string="Down Payment Amount",
        compute='_wilco_compute_downpayment_amounts'
    )
    wilco_amount_downpayment_deducted = fields.Monetary(
        string="Down Payment Deducted Amount",
        compute='_wilco_compute_downpayment_amounts'
    )

    @api.depends('payment_state', 'line_ids.matched_debit_ids', 'line_ids.matched_credit_ids')
    def _compute_wilco_payment_dates(self):
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
                move.wilco_payment_dates = False
                continue

            payment_dates = []
            # Get all the payment moves linked to this invoice
            for line in move.line_ids:
                # For customer invoices, check matched_credit_ids
                if move.move_type in ('out_invoice', 'out_refund'):
                    for partial in line.matched_credit_ids:
                        payment_move = partial.credit_move_id.move_id
                        if payment_move.payment_id and payment_move.date:
                            payment_dates.append(payment_move.date)
                # For vendor bills, check matched_debit_ids
                elif move.move_type in ('in_invoice', 'in_refund'):
                    for partial in line.matched_debit_ids:
                        payment_move = partial.debit_move_id.move_id
                        if payment_move.payment_id and payment_move.date:
                            payment_dates.append(payment_move.date)

            # Sort dates and format them
            if payment_dates:
                payment_dates = sorted(set(payment_dates))
                formatted_dates = [date.strftime('%Y-%m-%d') for date in payment_dates]
                move.wilco_payment_dates = ','.join(formatted_dates)
            else:
                move.wilco_payment_dates = False

    def _wilco_compute_settled_amounts(self):
        for order in self:
            order.wilco_amount_settled_total = order.amount_total - order.amount_residual
            order.wilco_amount_settled_total_signed = order.amount_total_signed - order.amount_residual_signed

    @api.depends('line_ids.is_downpayment', 'line_ids.price_subtotal', 'line_ids.display_type', 'line_ids.quantity')
    def _wilco_compute_downpayment_amounts(self):
        for move in self:
            downpayment_lines = move.line_ids.filtered(
                lambda line: line.quantity > 0 and line.is_downpayment
            )
            downpayment_deducted_lines = move.line_ids.filtered(
                lambda line: line.quantity < 0 and line.is_downpayment
            )
            move.wilco_amount_downpayment = sum(downpayment_lines.mapped('price_subtotal'))
            move.wilco_amount_downpayment_deducted = sum(downpayment_deducted_lines.mapped('price_subtotal'))

    @api.onchange('wilco_revision_no')
    def onchange_wilco_revision_no(self):
        if self.wilco_revision_no == 0:
            self.wilco_revision_date = False
        else:
            self.wilco_revision_date = fields.Date.today()

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
            if record.wilco_project_id and record.wilco_project_id.last_update_status:
                selection_dict = dict(project_model._fields['last_update_status'].selection or [])
                last_update_status_label = selection_dict.get(record.wilco_project_id.last_update_status, '')
                record.wilco_project_last_update_status = last_update_status_label
            else:
                record.wilco_project_last_update_status = ''


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

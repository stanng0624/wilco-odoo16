from odoo import api, fields, models

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    wilco_project_id = fields.Many2one(
        'project.project', string='Project', store=True, copy=False, readonly=False,
        compute='_wilco_compute_project_id')

    @api.depends('line_ids')
    def _wilco_compute_project_id(self):
        # for wizard in self:
        #     if wizard.can_edit_wizard:
        #         batches_result = wizard._get_batches()[0]
        #         wizard.wilco_project_id = wizard._wilco_get_project_id(batches_result)
        #     else:
        #         wizard.wilco_project_id = None
        # for wizard in self:
        for wizard in self:
            batches_result = wizard._get_batches()[0]
            wizard.wilco_project_id = wizard._wilco_get_project_id(batches_result)

    def _wilco_get_project_id(self, batch_result):
        self.ensure_one()
        wilco_project_id = None
        # for line in batch_result['lines']:
        #     if not wilco_project_id: #Get the first invoice's project ID
        #         wilco_project_id = line.wilco_project_id
        lines = batch_result['lines']
        wilco_project_id = lines.move_id[0].wilco_project_id #Get first project ID

        return wilco_project_id

    def _create_payment_vals_from_wizard(self, batch_result):
        # OVERRIDE
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        payment_vals['wilco_project_id'] = self.wilco_project_id.id
        return payment_vals
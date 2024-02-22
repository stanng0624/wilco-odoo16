from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        
        line_vals_list = super()._prepare_move_line_default_vals(write_off_line_vals)

        #Add project's analytic account
        if self.wilco_project_id and self.wilco_project_id.analytic_account_id.id:
            for line in line_vals_list:
                analytic_account_id = self.wilco_project_id.analytic_account_id.id
                analytic_distribution = {}
                if analytic_account_id:
                    analytic_account_id_str = str(analytic_account_id)
                    analytic_distribution = {analytic_account_id_str: 100}
                line.update({'analytic_distribution': analytic_distribution})

        return line_vals_list

    @api.model
    def _get_trigger_fields_to_synchronize(self):
        fields = super()._get_trigger_fields_to_synchronize()
        fields = fields + ('wilco_project_id', )
        return fields

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return
        
        super()._synchronize_from_moves(changed_fields)

        #Synchronize project code to journal entries/invoice/payment
        if 'wilco_project_id' in changed_fields:
            self._wilco_synchronize_from_moves_project_id()

    def _wilco_synchronize_from_moves_project_id(self):
        for pay in self.with_context(skip_account_move_synchronization=True):
            #Copy logic from account_payment._synchronize_from_moves()
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            move_vals_to_write.update({
                'wilco_project_id': pay.wilco_project_id,
            })
            payment_vals_to_write.update({
                'wilco_project_id': pay.wilco_project_id,
            })

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

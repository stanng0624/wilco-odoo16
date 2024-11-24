from odoo import models, api

class AccountGroup(models.Model):
    _inherit = 'account.group'

    def wilco_exist_in_account_groups(self, account_id, group_ids=None):
        """
        Check if an account belongs to specific account groups by IDs
        :param account_id: account.account record
        :param group_ids: list of account.group IDs
        :return: boolean
        """
        self.ensure_one()
        if not group_ids or not account_id:
            return False

        if isinstance(group_ids, (int, str)):
            group_ids = [int(group_ids)]
        
        account_groups = self.env['account.group'].sudo().browse(group_ids)
        
        for group in account_groups:
            account_code_prefix = account_id.code[0:len(group.code_prefix_start)]
            if (group.code_prefix_start <= account_code_prefix <= group.code_prefix_end):
                return True
        
        return False 
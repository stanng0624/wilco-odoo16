from odoo.tools.populate import compute

from odoo import api, fields, models, _


class AccountAnalyticAccountLine(models.Model):
    _inherit = 'account.analytic.line'

    wilco_amount_debit = fields.Monetary(string='Debit', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_amount_credit = fields.Monetary(string='Credit', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_is_receivable = fields.Boolean(string='Receivable', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_is_payable = fields.Boolean(string='Is Payable', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_is_payment = fields.Boolean(nastringme='Is Payment', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_is_revenue = fields.Boolean(string='Is Revenue', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_is_income = fields.Boolean(string='Is Income', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_is_cost = fields.Boolean(string='Is Cost', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_is_expense = fields.Boolean(string='Is Expense', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_amount_receivable = fields.Monetary(string='Receivable', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_amount_payable = fields.Monetary(string='Payable', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_amount_payment = fields.Monetary(string='Payment', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_amount_revenue = fields.Monetary(string='Revenue', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_amount_income = fields.Monetary(string='Income', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_amount_cost = fields.Monetary(string='Cost', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_amount_expense = fields.Monetary(string='Expense', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_amount_gross_profit = fields.Monetary(string='Gross Profit', compute='_wilco_compute_amounts', store=True, readonly=True)
    wilco_amount_net_profit = fields.Monetary(string='Net Profit', compute='_wilco_compute_amounts', store=True, readonly=True)
    # Performance issue if not using store field
    # wilco_amount_debit = fields.Monetary(string='Debit', compute='_wilco_compute_amounts')
    # wilco_amount_credit = fields.Monetary(string='Credit', compute='_wilco_compute_amounts')
    # wilco_is_receivable = fields.Boolean(string='Receivable', compute='_wilco_compute_amounts')
    # wilco_is_payable = fields.Boolean(string='Is Payable', compute='_wilco_compute_amounts')
    # wilco_is_payment = fields.Boolean(nastringme='Is Payment', compute='_wilco_compute_amounts')
    # wilco_is_revenue = fields.Boolean(string='Is Revenue', compute='_wilco_compute_amounts')
    # wilco_is_income = fields.Boolean(string='Is Income', compute='_wilco_compute_amounts')
    # wilco_is_cost = fields.Boolean(string='Is Cost', compute='_wilco_compute_amounts')
    # wilco_is_expense = fields.Boolean(string='Is Expense', compute='_wilco_compute_amounts')
    # wilco_amount_receivable = fields.Monetary(string='Receivable', compute='_wilco_compute_amounts')
    # wilco_amount_payable = fields.Monetary(string='Payable', compute='_wilco_compute_amounts')
    # wilco_amount_payment = fields.Monetary(string='Payment', compute='_wilco_compute_amounts')
    # wilco_amount_revenue = fields.Monetary(string='Revenue', compute='_wilco_compute_amounts')
    # wilco_amount_income = fields.Monetary(string='Income', compute='_wilco_compute_amounts')
    # wilco_amount_cost = fields.Monetary(string='Cost', compute='_wilco_compute_amounts')
    # wilco_amount_expense = fields.Monetary(string='Expense', compute='_wilco_compute_amounts')
    # wilco_amount_gross_profit = fields.Monetary(string='Gross Profit', compute='_wilco_compute_amounts')
    # wilco_amount_net_profit = fields.Monetary(string='Net Profit', compute='_wilco_compute_amounts')
    #
    # @api.model
    # def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
    #     """
    #         Override read_group to calculate the sum of the non-stored fields that depend on the user context
    #     """
    #     res = super(AccountAnalyticAccountLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
    #                                                              orderby=orderby, lazy=lazy)
    #     analytic_lines = self.env['account.analytic.line']
    #     for line in res:
    #         if '__domain' in line:
    #             analytic_lines = self.search(line['__domain'])
    #         if 'wilco_amount_receivable' in fields:
    #             line['wilco_amount_receivable'] = sum(analytic_lines.mapped('wilco_amount_receivable'))
    #         if 'wilco_amount_payable' in fields:
    #             line['wilco_amount_payable'] = sum(analytic_lines.mapped('wilco_amount_payable'))
    #         if 'wilco_amount_payment' in fields:
    #             line['wilco_amount_payment'] = sum(analytic_lines.mapped('wilco_amount_payment'))
    #         if 'wilco_amount_revenue' in fields:
    #             line['wilco_amount_revenue'] = sum(analytic_lines.mapped('wilco_amount_revenue'))
    #         if 'wilco_amount_revenue' in fields:
    #             line['wilco_amount_income'] = sum(analytic_lines.mapped('wilco_amount_income'))
    #         if 'wilco_amount_cost' in fields:
    #             line['wilco_amount_cost'] = sum(analytic_lines.mapped('wilco_amount_cost'))
    #         if 'wilco_amount_expense' in fields:
    #             line['wilco_amount_expense'] = sum(analytic_lines.mapped('wilco_amount_expense'))
    #         if 'wilco_amount_gross_profit' in fields:
    #             line['wilco_amount_gross_profit'] = sum(analytic_lines.mapped('wilco_amount_gross_profit'))
    #         if 'wilco_amount_net_profit' in fields:
    #             line['wilco_amount_net_profit'] = sum(analytic_lines.mapped('wilco_amount_net_profit'))
    #     return res

    @api.depends('amount', 'general_account_id')
    def _wilco_compute_amounts(self):
        for line in self:
            line.wilco_is_payable = False
            line.wilco_is_receivable = False
            line.wilco_is_payment = False
            line.wilco_is_revenue = False
            line.wilco_is_income = False
            line.wilco_is_cost = False
            line.wilco_is_expense = False

            account_code_prefix = line.general_account_id.code[0:2]
            # if account_code_prefix == '41':
            #     test_info = account_code_prefix

            if self._wilco_exist_in_account_groups(line.general_account_id, group_name='Accounts Receivable'):
                line.wilco_is_receivable = True
            if self._wilco_exist_in_account_groups(line.general_account_id, group_name='Accounts Payable'):
                line.wilco_is_payable = True
            if self._wilco_exist_in_account_groups(line.general_account_id, group_name='Other Payable'):
                line.wilco_is_payable = True
            if self._wilco_exist_in_account_groups(line.general_account_id, group_name='Bank'):
                line.wilco_is_payment = True
            if self._wilco_exist_in_account_groups(line.general_account_id, group_name='Cash'):
                line.wilco_is_payment = True
            if self._wilco_exist_in_account_groups(line.general_account_id, group_name='Revenue'):
                line.wilco_is_revenue = True
            if self._wilco_exist_in_account_groups(line.general_account_id, group_name='Costs'):
                line.wilco_is_cost = True
            if self._wilco_exist_in_account_groups(line.general_account_id, group_name='Income'):
                line.wilco_is_income = True
            if self._wilco_exist_in_account_groups(line.general_account_id, group_name='Expense'):
                line.wilco_is_expense = True

            line.wilco_amount_credit = 0
            line.wilco_amount_debit = 0
            line.wilco_amount_receivable = 0
            line.wilco_amount_payable = 0
            line.wilco_amount_payment = 0
            line.wilco_amount_revenue = 0
            line.wilco_amount_income = 0
            line.wilco_amount_debit = 0
            line.wilco_amount_cost = 0
            line.wilco_amount_expense = 0
            line.wilco_amount_gross_profit = 0
            line.wilco_amount_net_profit = 0

            # line.amount positive is Credit, negative is Debit
            # Reverse sign to convert back to normal G/L entry amount
            # G/L entry amount is Debit = Postive, Credit = Negative
            #Asset account, Debit = Increase, Credit =  Decrease
            gl_amount = -line.amount

            if gl_amount > 0:
                line.wilco_amount_debit = gl_amount
            else:
                line.wilco_amount_credit = -gl_amount

            if line.wilco_is_receivable:
                line.wilco_amount_receivable = gl_amount
            if line.wilco_is_payment:
                line.wilco_amount_payment = gl_amount
            # Liability account, Debit = Decrease, Credit =  Decrease
            if line.wilco_is_payable:
                line.wilco_amount_payable = -gl_amount
            # Profit and lost account, Debit = Decrease, Credit =  Increase
            if line.wilco_is_revenue:
                line.wilco_amount_revenue = -gl_amount
            if line.wilco_is_income:
                line.wilco_amount_income = -gl_amount
            if line.wilco_is_cost:
                line.wilco_amount_cost = gl_amount
            if line.wilco_is_expense:
                line.wilco_amount_expense = gl_amount

            line.wilco_amount_gross_profit = line.wilco_amount_revenue - line.wilco_amount_cost
            line.wilco_amount_net_profit = line.wilco_amount_gross_profit \
                                         + line.wilco_amount_income \
                                         - line.wilco_amount_expense

    def _wilco_exist_in_account_groups(self, account_id, group_name=''):
        if not group_name:
            return False
        if not account_id:
            return False

        account_group = self.env['account.group'].sudo().search([
            ('name', '=', group_name),
        ], limit=1)

        if not account_group.id:
            return False

        account_code_prefix = account_id.code[0:len(account_group.code_prefix_start)]
        if account_group.code_prefix_start >= account_code_prefix\
        and account_group.code_prefix_end <= account_code_prefix:
            return True
        return False

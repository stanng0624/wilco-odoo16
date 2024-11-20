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
            line._wilco_set_amount_status_fields()
            line._wilco_calc_amounts()

    def _wilco_set_amount_status_fields(self):
        self.ensure_one()

        # Dictionary mapping status fields to account groups or sets of groups
        account_group_mapping = {
            'wilco_is_receivable': 'Accounts Receivable',
            'wilco_is_payable': {'Accounts Payable', 'Other Payable'},
            'wilco_is_payment': {'Bank', 'Cash'},
            'wilco_is_revenue': 'Revenue',
            'wilco_is_income': 'Income',
            'wilco_is_cost': 'Costs',
            'wilco_is_expense': 'Expense',
        }

        # Reset all status fields to False at the initial stage
        for field in account_group_mapping:
            setattr(self, field, False)

        # Iterate over the account group mapping and set fields based on group existence
        for field, groups in account_group_mapping.items():
            if isinstance(groups, str):
                # Single group case
                if self._wilco_exist_in_account_groups(self.general_account_id, group_name=groups):
                    setattr(self, field, True)
            elif isinstance(groups, set):
                # Multiple groups case
                if any(self._wilco_exist_in_account_groups(self.general_account_id, group_name=group) for group in
                       groups):
                    setattr(self, field, True)

    def _wilco_calc_amounts(self):
        self.ensure_one()

        self.wilco_amount_credit = 0
        self.wilco_amount_debit = 0
        self.wilco_amount_receivable = 0
        self.wilco_amount_payable = 0
        self.wilco_amount_payment = 0
        self.wilco_amount_revenue = 0
        self.wilco_amount_income = 0
        self.wilco_amount_debit = 0
        self.wilco_amount_cost = 0
        self.wilco_amount_expense = 0
        self.wilco_amount_gross_profit = 0
        self.wilco_amount_net_profit = 0

        # line.amount positive is Credit, negative is Debit
        # Reverse sign to convert back to normal G/L entry amount
        # G/L entry amount is Debit = Postive, Credit = Negative
        #Asset account, Debit = Increase, Credit =  Decrease
        gl_amount = -self.amount

        if gl_amount > 0:
            self.wilco_amount_debit = gl_amount
        else:
            self.wilco_amount_credit = -gl_amount

        if self.wilco_is_receivable:
            self.wilco_amount_receivable = gl_amount
        if self.wilco_is_payment:
            self.wilco_amount_payment = gl_amount
        # Liability account, Debit = Decrease, Credit =  Decrease
        if self.wilco_is_payable:
            self.wilco_amount_payable = -gl_amount
        # Profit and lost account, Debit = Decrease, Credit =  Increase
        if self.wilco_is_revenue:
            self.wilco_amount_revenue = -gl_amount
        if self.wilco_is_income:
            self.wilco_amount_income = -gl_amount
        if self.wilco_is_cost:
            self.wilco_amount_cost = gl_amount
        if self.wilco_is_expense:
            self.wilco_amount_expense = gl_amount

        self.wilco_amount_gross_profit = self.wilco_amount_revenue - self.wilco_amount_cost
        self.wilco_amount_net_profit = self.wilco_amount_gross_profit \
                                     + self.wilco_amount_income \
                                     - self.wilco_amount_expense

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
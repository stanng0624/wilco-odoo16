from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class AccountAgedAnalyticBalance(models.TransientModel):
    _name = 'account.aged.analytic.balance'
    _description = 'Account Aged Analytic Balance Report'
    _inherit = 'account.common.partner.report'

    period_length = fields.Integer(string='Period Length (days)', required=True, default=30)
    date_from = fields.Date(default=fields.Date.context_today)
    result_selection = fields.Selection([
        ('customer', 'Receivable'),
        ('supplier', 'Payable'),
        ('customer_supplier', 'Receivable and Payable')
    ], string='Account Type', required=True, default='customer')
    analytic_account_ids = fields.Many2many('account.analytic.account', 
        string='Analytic Accounts',
        required=False)

    def _get_report_data(self, data):
        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length', 'date_from', 'result_selection', 'analytic_account_ids'])[0])
        period_length = data['form']['period_length']
        if period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = data['form']['date_from']
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (str((5 - (i + 1)) * period_length) + '-' + str((5 - i) * period_length)) or ('+' + str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data['form'].update(res)
        return data

    def _print_report(self, data):
        data = self._get_report_data(data)
        return self.env.ref('wilco_project.action_report_aged_analytic_balance').report_action(self, data=data) 
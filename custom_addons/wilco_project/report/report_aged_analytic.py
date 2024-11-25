# -*- coding: utf-8 -*-

import time
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ReportAgedAnalyticBalance(models.AbstractModel):
    _name = 'report.wilco_project.report_aged_analytic'
    _description = 'Aged Analytic Balance Report'

    def _get_analytic_move_lines(self, account_type, analytic_account_ids,
                              date_from, target_move, period_length):
        periods = {}
        date_from = datetime.strptime(str(date_from), "%Y-%m-%d").date()
        start = datetime.strptime(str(date_from), "%Y-%m-%d")
        
        # Define periods like aged partner balance
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)  # Removed +1
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        # Initialize results
        analytic_lines = {}
        totals = [0] * 7  # [Not due, 0-30, 30-60, 60-90, 90-120, +120, Total]

        # Query for not due amounts (future dates)
        query_future = """
            SELECT aml.analytic_distribution, aml.balance as amount
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            JOIN account_account acc ON acc.id = aml.account_id
            WHERE am.state IN %s
                AND acc.account_type IN %s
                AND (COALESCE(aml.date_maturity,aml.date) >= %s)
                AND aml.analytic_distribution IS NOT NULL
                AND aml.date <= %s
        """
        
        move_state = ['posted'] if target_move == 'posted' else ['draft', 'posted']
        self.env.cr.execute(query_future, (tuple(move_state), tuple(account_type), date_from, date_from))
        
        # Rest of your existing code...

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        target_move = data['form'].get('target_move', 'all')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))

        if data['form']['result_selection'] == 'customer':
            account_type = ['asset_receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['liability_payable']
        else:
            account_type = ['asset_receivable', 'liability_payable']

        movelines, total, periods = self._get_analytic_move_lines(
            account_type,
            data['form'].get('analytic_account_ids', []),
            date_from,
            target_move,
            data['form'].get('period_length', 30)
        )

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_analytic_lines': movelines,
            'get_direction': total,
            'periods': periods
        }
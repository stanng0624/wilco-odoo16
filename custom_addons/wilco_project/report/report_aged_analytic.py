# -*- coding: utf-8 -*-

import time
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ReportAgedAnalyticBalance(models.AbstractModel):
    _name = 'report.wilco_project.report_agedanalyticbalance'
    _description = 'Aged Analytic Balance Report'

    def _get_analytic_move_lines(self, account_type, analytic_account_ids, date_from, target_move, period_length):
        periods = {}
        start = datetime.strptime(str(date_from), "%Y-%m-%d")
        date_from = datetime.strptime(str(date_from), "%Y-%m-%d").date()

        # Process periods in correct order (0-30, 30-60, etc.)
        for i in range(5):
            stop = start - relativedelta(days=period_length)
            period_name = str(i * period_length) + '-' + str((i + 1) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 4:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i != 4 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        # Initialize results
        analytic_lines = {}
        totals = [0] * 7

        # Query for move lines
        move_state = ['posted'] if target_move == 'posted' else ['draft', 'posted']
        query = '''
            SELECT aml.id
            FROM account_move_line aml
            JOIN account_move am ON (am.id = aml.move_id)
            JOIN account_account acc ON (aml.account_id = acc.id)
            WHERE (aml.date <= %s) AND (am.state IN %s)
            AND (acc.account_type IN %s)
            AND aml.analytic_distribution IS NOT NULL
        '''
        params = (date_from, tuple(move_state), tuple(account_type))
        self.env.cr.execute(query, params)
        aml_ids = [x[0] for x in self.env.cr.fetchall()]

        # Process each move line
        for line in self.env['account.move.line'].browse(aml_ids):
            analytic_dist = line.analytic_distribution or {}
            for analytic_id, percentage in analytic_dist.items():
                if not analytic_account_ids or int(analytic_id) in analytic_account_ids:
                    analytic_id = int(analytic_id)
                    if analytic_id not in analytic_lines:
                        analytic_name = self.env['account.analytic.account'].browse(analytic_id).name
                        analytic_lines[analytic_id] = {
                            'name': analytic_name,
                            'lines': [0] * 7,
                            'total': 0.0,
                        }

                    amount = line.balance * (percentage / 100.0)
                    date = line.date_maturity or line.date
                    period = 6

                    if date <= date_from:
                        for i in range(5):
                            stop = periods[str(i)]['stop']
                            start = periods[str(i)]['start']
                            if start and stop and start <= date.strftime('%Y-%m-%d') <= stop:
                                period = i
                                break
                        if period == 6:
                            period = 0

                    analytic_lines[analytic_id]['lines'][period] += amount
                    analytic_lines[analytic_id]['total'] += amount
                    totals[period] += amount

        # Convert periods dictionary to list in correct order
        periods_list = []
        for i in range(5):
            periods_list.append(periods[str(i)])

        return list(analytic_lines.values()), totals, periods_list

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        data['computed'] = {}
        obj_partner = self.env['res.partner']
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
            data['form']['period_length']
        )

        return {
            'doc_ids': data['form'].get('analytic_account_ids', []),
            'doc_model': 'account.analytic.account',
            'data': data['form'],
            'docs': self.env['account.analytic.account'].browse(data['form'].get('analytic_account_ids', [])),
            'time': time,
            'get_analytic_lines': movelines,
            'get_direction': total,
            'periods': periods,
        }
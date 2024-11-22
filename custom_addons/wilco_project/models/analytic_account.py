from odoo import api, fields, models, _


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    balance = fields.Monetary(string='G/L Balance') #Override the label

    wilco_project_id = fields.Many2one(
        comodel_name='project.project',
        string="Related Project",
        compute='_wilco_compute_project_id')
    wilco_project_stage_id = fields.Many2one(
        comodel_name='project.project.stage',
        related="wilco_project_id.stage_id", string="Project Stage", readonly=True)
    wilco_project_last_update_status = fields.Selection(
        related="wilco_project_id.last_update_status",
        string="Project Status", readonly=True)

    wilco_sale_order_count = fields.Integer(string="Sales Order Count", compute='_wilco_compute_sale_order_count')

    wilco_amount_receivable = fields.Monetary(string='Receivable', compute='_wilco_compute_amounts')
    wilco_amount_payable = fields.Monetary(string='Payable', compute='_wilco_compute_amounts')
    wilco_amount_payment = fields.Monetary(string='Payment', compute='_wilco_compute_amounts')
    wilco_amount_revenue = fields.Monetary(string='Revenue', compute='_wilco_compute_amounts')
    wilco_amount_income = fields.Monetary(string='Income', compute='_wilco_compute_amounts')
    wilco_amount_cost = fields.Monetary(string='Cost', compute='_wilco_compute_amounts')
    wilco_amount_expense = fields.Monetary(string='Expense', compute='_wilco_compute_amounts')
    wilco_amount_gross_profit = fields.Monetary(string='Gross Profit', compute='_wilco_compute_amounts')
    wilco_amount_net_profit = fields.Monetary(string='Net Profit', compute='_wilco_compute_amounts')
    # wilco_amount_budget_cost_total = fields.Monetary(string="Budget cost", compute='_wilco_compute_amounts')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
            Override read_group to calculate the sum of the non-stored fields that depend on the user context
        """
        res = super(AccountAnalyticAccount, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                             orderby=orderby, lazy=lazy)
        accounts = self.env['account.analytic.account']
        for line in res:
            if '__domain' in line:
                accounts = self.search(line['__domain'])
            if 'vendor_bill_count' in fields:
                line['vendor_bill_count'] = sum(accounts.mapped('vendor_bill_count'))
            if 'invoice_count' in fields:
                line['invoice_count'] = sum(accounts.mapped('invoice_count'))
            if 'wilco_sale_order_count' in fields:
                line['wilco_sale_order_count'] = sum(accounts.mapped('wilco_sale_order_count'))
            if 'wilco_amount_receivable' in fields:
                line['wilco_amount_receivable'] = sum(accounts.mapped('wilco_amount_receivable'))
            if 'wilco_amount_payable' in fields:
                line['wilco_amount_payable'] = sum(accounts.mapped('wilco_amount_payable'))
            if 'wilco_amount_payment' in fields:
                line['wilco_amount_payment'] = sum(accounts.mapped('wilco_amount_payment'))
            if 'wilco_amount_revenue' in fields:
                line['wilco_amount_revenue'] = sum(accounts.mapped('wilco_amount_revenue'))
            if 'wilco_amount_income' in fields:
                line['wilco_amount_income'] = sum(accounts.mapped('wilco_amount_income'))
            if 'wilco_amount_cost' in fields:
                line['wilco_amount_cost'] = sum(accounts.mapped('wilco_amount_cost'))
            if 'wilco_amount_expense' in fields:
                line['wilco_amount_expense'] = sum(accounts.mapped('wilco_amount_expense'))
            if 'wilco_amount_gross_profit' in fields:
                line['wilco_amount_gross_profit'] = sum(accounts.mapped('wilco_amount_gross_profit'))
            if 'wilco_amount_net_profit' in fields:
                line['wilco_amount_net_profit'] = sum(accounts.mapped('wilco_amount_net_profit'))
            if 'wilco_amount_budget_cost_total' in fields:
                line['wilco_amount_budget_cost_total'] = sum(accounts.mapped('wilco_amount_budget_cost_total'))

        return res

    def _wilco_compute_project_id(self):
        for record in self:
            # Search for the project where analytic_account_id matches the current analytic account
            project = self.env['project.project'].search([('analytic_account_id', '=', record.id)], limit=1)
            record.wilco_project_id = project.id

    @api.depends('line_ids')
    def _wilco_compute_amounts(self):
        for account in self:
            lines = account.line_ids.filtered(lambda line: line.account_id != account.id)
            amount_receivable = sum(lines.mapped("wilco_amount_receivable"))
            amount_payable = sum(lines.mapped("wilco_amount_payable"))
            amount_payment = sum(lines.mapped("wilco_amount_payment"))
            amount_revenue = sum(lines.mapped("wilco_amount_revenue"))
            amount_income = sum(lines.mapped("wilco_amount_income"))
            amount_cost = sum(lines.mapped("wilco_amount_cost"))
            amount_expense = sum(lines.mapped("wilco_amount_expense"))
            amount_gross_profit = sum(lines.mapped("wilco_amount_gross_profit"))
            amount_net_profit = sum(lines.mapped("wilco_amount_net_profit"))

            #Assume all are in same currency first
            account.wilco_amount_receivable = amount_receivable
            account.wilco_amount_payable = amount_payable
            account.wilco_amount_payment = amount_payment
            account.wilco_amount_revenue = amount_revenue
            account.wilco_amount_income = amount_income
            account.wilco_amount_cost = amount_cost
            account.wilco_amount_expense = amount_expense
            account.wilco_amount_gross_profit = amount_gross_profit
            account.wilco_amount_net_profit = amount_net_profit

            # sale_order_lines = self.env['sale.order.line'].search([('analytic_line_ids.account_id', '=', account.id)])
            # # Sum the total amount of each sale order line (price_total)
            # account.wilco_amount_budget_cost_total = sum(line.wilco_amount_budget_cost_total for line in sale_order_lines)

    @api.depends('line_ids')
    def _wilco_compute_sale_order_count(self):
        for account in self:
            account.wilco_sale_order_count = self.env['sale.order'].search_count([
                ('order_line.invoice_lines.analytic_line_ids.account_id', '=', account.id)
            ])

    def wilco_action_view_sale_orders(self):
        self.ensure_one()
        sale_orders = self.env['sale.order'].search([
            ('order_line.invoice_lines.analytic_line_ids.account_id', '=', self.id)
        ])
        result = {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "domain": [['id', 'in', sale_orders.ids]],
            "name": _("Sale Orders"),
            'view_mode': 'tree,form',
        }
        if len(sale_orders) == 1:
            result['view_mode'] = 'form'
            result['res_id'] = sale_orders.id
        return result

    def wilco_action_view_analytic_lines(self):
        self.ensure_one()
        analytic_lines = self.env['account.analytic.line'].search([
            ('move_line_id.analytic_line_ids.account_id', '=', self.id)
        ])
        result = {
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.line",
            "domain": [['id', 'in', analytic_lines.ids]],
            "name": _("Analytic Items"),
            'view_mode': 'tree,form',
        }
        return result

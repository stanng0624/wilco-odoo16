from odoo import api, fields, models, _


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    balance = fields.Monetary(string='G/L Balance') #Override the label

    wilco_project_id = fields.Many2one(
        comodel_name='project.project',
        string="Related Project",
        compute='_wilco_compute_project_info')
    wilco_project_stage_id = fields.Many2one(
        comodel_name='project.project.stage',
        string="Project Stage",
        compute='_wilco_compute_project_info')
    wilco_project_last_update_status = fields.Char(
        string="Project Status",
        compute='_wilco_compute_project_info')

    wilco_sale_order_count = fields.Integer(string="Sales Order Count", compute='_wilco_compute_sale_order_count')

    wilco_amount_receivable = fields.Monetary(string='Receivable', compute='_wilco_compute_amounts')
    wilco_amount_payable = fields.Monetary(string='Payable', compute='_wilco_compute_amounts')
    wilco_amount_payment = fields.Monetary(string='Actual Cash Flow', compute='_wilco_compute_amounts')
    wilco_amount_payment_received = fields.Monetary(string='Cash In', compute='_wilco_compute_amounts')
    wilco_amount_payment_issued = fields.Monetary(string='Cash Out', compute='_wilco_compute_amounts')
    wilco_amount_revenue = fields.Monetary(string='Revenue', compute='_wilco_compute_amounts')
    wilco_amount_income = fields.Monetary(string='Income', compute='_wilco_compute_amounts')
    wilco_amount_cost = fields.Monetary(string='Cost', compute='_wilco_compute_amounts')
    wilco_amount_expense = fields.Monetary(string='Expense', compute='_wilco_compute_amounts')
    wilco_amount_gross_profit = fields.Monetary(string='Gross Profit', compute='_wilco_compute_amounts')
    wilco_gross_profit_percent = fields.Float(string="Actual GP%", compute='_wilco_compute_amounts')
    wilco_amount_net_profit = fields.Monetary(string='Net Profit', compute='_wilco_compute_amounts')
    wilco_net_profit_percent = fields.Float(string="Actual NP%", compute='_wilco_compute_amounts')
    wilco_amount_budget_cost_total = fields.Monetary(string="Budget cost", compute='_wilco_compute_amounts')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
        Override read_group to calculate the sum of the non-stored fields that depend on the user context
        """
        res = super(AccountAnalyticAccount, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                           orderby=orderby, lazy=lazy)
        
        # Define fields to sum
        sum_fields = [
            'vendor_bill_count',
            'invoice_count',
            'wilco_sale_order_count',
            'wilco_amount_receivable',
            'wilco_amount_payable',
            'wilco_amount_payment',
            'wilco_amount_revenue',
            'wilco_amount_income',
            'wilco_amount_cost',
            'wilco_amount_expense',
            'wilco_amount_gross_profit',
            'wilco_amount_net_profit',
            'wilco_amount_budget_cost_total',
            'wilco_amount_payment_received',
            'wilco_amount_payment_issued',
        ]

        accounts = self.env['account.analytic.account']
        for line in res:
            if '__domain' in line:
                accounts = self.search(line['__domain'])
            
            # Sum all requested fields that are in our sum_fields list
            for field in sum_fields:
                if field in fields:
                    line[field] = sum(accounts.mapped(field))

        return res

    def _wilco_compute_project_info(self):
        for record in self:
            if record.id:
                project_model = self.env['project.project']
                project = project_model.search([('analytic_account_id', '=', record.id)], limit=1)

                record.wilco_project_id = project.id
                record.wilco_project_stage_id = project.stage_id

                last_update_status_label = dict(project_model._fields['last_update_status'].selection).get(project.last_update_status, False)
                record.wilco_project_last_update_status = last_update_status_label

    @api.depends('line_ids')
    def _wilco_compute_amounts(self):
        for account in self:
            amount_receivable = 0
            amount_payable = 0
            amount_payment = 0
            amount_revenue = 0
            amount_income = 0
            amount_cost = 0
            amount_expense = 0
            amount_gross_profit = 0
            amount_net_profit = 0
            amount_payment_received = 0
            amount_payment_issued = 0

            lines = account.line_ids
            if lines:
                amount_receivable = sum(lines.mapped("wilco_amount_receivable"))
                amount_payable = sum(lines.mapped("wilco_amount_payable"))
                amount_payment = sum(lines.mapped("wilco_amount_payment"))
                amount_revenue = sum(lines.mapped("wilco_amount_revenue"))
                amount_income = sum(lines.mapped("wilco_amount_income"))
                amount_cost = sum(lines.mapped("wilco_amount_cost"))
                amount_expense = sum(lines.mapped("wilco_amount_expense"))
                amount_gross_profit = sum(lines.mapped("wilco_amount_gross_profit"))
                amount_net_profit = sum(lines.mapped("wilco_amount_net_profit"))
                amount_payment_received = sum(lines.mapped("wilco_amount_payment_received"))
                amount_payment_issued = sum(lines.mapped("wilco_amount_payment_issued"))

            #Assume all are in same currency first
            account.wilco_amount_receivable = amount_receivable
            account.wilco_amount_payable = amount_payable
            account.wilco_amount_payment = amount_payment
            account.wilco_amount_revenue = amount_revenue
            account.wilco_amount_income = amount_income
            account.wilco_amount_cost = amount_cost
            account.wilco_amount_expense = amount_expense
            account.wilco_amount_gross_profit = amount_gross_profit
            account.wilco_gross_profit_percent = (amount_revenue - amount_cost) / amount_revenue if amount_revenue != 0 else 0.0
            account.wilco_amount_net_profit = amount_net_profit
            account.wilco_net_profit_percent = amount_net_profit / amount_revenue if amount_revenue != 0 else 0.0
            account.wilco_amount_payment_received = amount_payment_received
            account.wilco_amount_payment_issued = amount_payment_issued

            # No analytic account will be created from sales order
            # sale_order_lines = self.env[
            #     'sale.order.line'].search([
            #     ('analytic_line_ids.account_id', 'in', [account.id])
            # ])
            sale_order_lines = self.env['sale.order.line'].search([
                ('analytic_distribution', 'ilike', account.id)
            ])
            # Sum the total amount of each sale order line (price_total)
            account.wilco_amount_budget_cost_total = sum(line.wilco_amount_budget_cost_total for line in sale_order_lines)

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

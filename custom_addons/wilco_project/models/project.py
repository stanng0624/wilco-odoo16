from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.wilco_project.utils.external_identifier_util import ExternalIdentifierUtil

class Project(models.Model):
    _inherit = 'project.project'

    name = fields.Char(string='Project Number')
    # Revise 'to_define' label from 'Set Status' to 'No Status'
    last_update_status = fields.Selection(
        selection=[
            ('on_track', 'On Track'),
            ('at_risk', 'At Risk'),
            ('off_track', 'Off Track'),
            ('on_hold', 'On Hold'),
            ('to_define', 'No Status'),
        ])

    wilco_project_name = fields.Char(string='Project Name', translate=True, index=True)
    wilco_date_award = fields.Date(string='Award Date')

    # Computed fields for Project Status Listing Report
    wilco_total_contract_sum = fields.Monetary(
        string='Total Contract Sum',
        compute='_wilco_compute_project_financials',
        help='Sum of confirmed sales orders')
    wilco_total_invoice_amount = fields.Monetary(
        string='Total Invoice Amount',
        compute='_wilco_compute_project_financials',
        help='Sum of customer invoices')
    wilco_invoice_percent = fields.Float(
        string='Invoice %',
        compute='_wilco_compute_project_financials',
        help='Invoice amount as percentage of contract sum')
    wilco_total_budget_cost = fields.Monetary(
        string='Total Budget Cost',
        compute='_wilco_compute_project_financials',
        help='Sum of budgeted costs from sales orders')
    wilco_total_vendor_bill_amount = fields.Monetary(
        string='Total Vendor Bill Amount',
        compute='_wilco_compute_project_financials',
        help='Sum of vendor bills for project')
    wilco_vendor_bill_percent = fields.Float(
        string='Vendor Bill %',
        compute='_wilco_compute_project_financials',
        help='Vendor bill amount as percentage of budget cost')
    wilco_total_cost_expense = fields.Monetary(
        string='Total Cost & Expense',
        compute='_wilco_compute_project_financials',
        help='Total cost and expense from analytic lines')
    wilco_cost_expense_percent = fields.Float(
        string='Cost & Expense %',
        compute='_wilco_compute_project_financials',
        help='Cost and expense as percentage of budget cost')
    wilco_estimated_gp_percent = fields.Float(
        string='Estimated GP%',
        compute='_wilco_compute_project_financials',
        help='Estimated gross profit percentage')
    wilco_project_pnl = fields.Monetary(
        string='Project P&L',
        compute='_wilco_compute_project_financials',
        help='Net profit from analytic distribution')
    wilco_actual_np_percent = fields.Float(
        string='Actual NP%',
        compute='_wilco_compute_project_financials',
        help='Actual net profit percentage')
    wilco_actual_cash_flow = fields.Monetary(
        string='Actual Cash Flow',
        compute='_wilco_compute_project_financials',
        help='Net payment from analytic distribution')
    wilco_cash_flow_percent = fields.Float(
        string='Cash Flow %',
        compute='_wilco_compute_project_financials',
        help='Cash flow as percentage of invoice amount')

    @api.constrains('name')
    def _wilco_check_name(self):
        for project in self:
            if not project.name:
                continue

            if ' ' in project.name:
                raise UserError("Project Number cannot contain space.")

            project_check_exist_name = self.env['project.project'].search([
                ('name', '=', project.name),
                ('id', '!=', self.id),
            ], limit=1)
            if project_check_exist_name:
                raise UserError("Project Number '{}' has already been used by another project (Project Name: {}).".format(
                    project.name, project_check_exist_name.wilco_project_name))

    def name_get(self):
        result = []
        for project in self:
            name = ""
            if project.wilco_project_name:
                name = f"{project.name} {project.wilco_project_name}"
            else:
                name = project.name
            result.append((project.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('wilco_project_name', operator, name)]
        project_ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return list(project_ids)

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)

        for project in result:
            if not project.analytic_account_id:
                project._create_analytic_account()

            if project.name and not ExternalIdentifierUtil.exist_external_identifier(
                self.env, self._name, project.id):
                ExternalIdentifierUtil.write_external_identifier(
                    self.env, self._name, project.id, project.name)

        return result

    def write(self, vals):
        result = super(Project, self).write(vals)

        if 'partner_id' in vals and self.analytic_account_id:
            projects_read_group = self.env['project.project']._read_group(
                [('analytic_account_id', 'in', self.analytic_account_id.ids)],
                ['analytic_account_id'],
                ['analytic_account_id']
            )
            analytic_account_to_update = self.env['account.analytic.account'].browse([
                result['analytic_account_id'][0]
                for result in projects_read_group
                if result['analytic_account_id'] and result['analytic_account_id_count'] == 1
            ])
            analytic_account_to_update.write({'partner_id': self.partner_id})

        for project in self:
            if not project.analytic_account_id:
                project._create_analytic_account()

            if 'name' in vals and project.name:
                ExternalIdentifierUtil.write_external_identifier(
                    self.env, self._name, project.id, project.name)

        return result

    @api.depends('partner_id', 'analytic_account_id')
    def _wilco_compute_project_financials(self):
        """
        Compute financial metrics for project status listing report.
        These are calculated on-demand (not stored) to ensure real-time accuracy.
        """
        for project in self:
            # Get sales orders for this project
            sale_orders = self.env['sale.order'].search([
                ('wilco_project_id', '=', project.id),
                ('state', 'in', ['sale', 'done'])
            ])

            # Get customer invoices
            customer_invoices = self.env['account.move'].search([
                ('wilco_project_id', '=', project.id),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', 'in', ['posted'])
            ])

            # Get analytic lines for this project
            analytic_lines = self.env['account.analytic.line'].search([
                ('account_id', '=', project.analytic_account_id.id)
            ]) if project.analytic_account_id else self.env['account.analytic.line']

            # Get vendor bills (both direct link and via analytic distribution)
            vendor_bills_with_project = self.env['account.move'].search([
                ('wilco_project_id', '=', project.id),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', 'in', ['posted']),
                ('expense_sheet_id', '=', False)
            ])

            vendor_bills_no_project = self.env['account.move'].search([
                ('wilco_project_id', '=', False),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', 'in', ['posted']),
                ('expense_sheet_id', '=', False)
            ])

            # Filter vendor bills with matching analytic distribution
            vendor_bills_with_analytic = self.env['account.move']
            if project.analytic_account_id:
                analytic_account_str = str(project.analytic_account_id.id)
                for bill in vendor_bills_no_project:
                    if any(line.analytic_distribution and analytic_account_str in line.analytic_distribution 
                           for line in bill.invoice_line_ids):
                        vendor_bills_with_analytic |= bill

            vendor_bills = vendor_bills_with_project | vendor_bills_with_analytic

            # Calculate totals
            project.wilco_total_contract_sum = sum(sale_orders.mapped('amount_total'))
            project.wilco_total_invoice_amount = sum(customer_invoices.mapped('amount_total'))
            project.wilco_total_budget_cost = sum(sale_orders.mapped('wilco_amount_budget_cost_total'))

            # Calculate percentages
            project.wilco_invoice_percent = (
                (project.wilco_total_invoice_amount / project.wilco_total_contract_sum * 100)
                if project.wilco_total_contract_sum != 0 else 0.0
            )

            # Calculate vendor bill amount (accounting for partial project bills)
            total_vendor_bill_amount = 0.0
            if project.analytic_account_id:
                analytic_account_str = str(project.analytic_account_id.id)
                for bill in vendor_bills:
                    if bill.wilco_project_id:
                        # Bill directly linked to project
                        total_vendor_bill_amount += bill.amount_total
                    else:
                        # Bill with analytic distribution - only count project portion
                        for line in bill.invoice_line_ids:
                            if line.analytic_distribution and analytic_account_str in line.analytic_distribution:
                                total_vendor_bill_amount += line.price_total

            project.wilco_total_vendor_bill_amount = total_vendor_bill_amount
            project.wilco_vendor_bill_percent = (
                (project.wilco_total_vendor_bill_amount / project.wilco_total_budget_cost * 100)
                if project.wilco_total_budget_cost != 0 else 0.0
            )

            # Calculate cost and expense from analytic lines
            total_cost_expense = sum(
                (line.wilco_amount_cost or 0.0) + (line.wilco_amount_expense or 0.0)
                for line in analytic_lines
            )
            project.wilco_total_cost_expense = total_cost_expense
            project.wilco_cost_expense_percent = (
                (total_cost_expense / project.wilco_total_budget_cost * 100)
                if project.wilco_total_budget_cost != 0 else 0.0
            )

            # Calculate profit metrics
            project.wilco_estimated_gp_percent = (
                ((project.wilco_total_contract_sum - project.wilco_total_budget_cost) / 
                 project.wilco_total_contract_sum * 100)
                if project.wilco_total_contract_sum != 0 else 0.0
            )

            total_net_profit = sum(analytic_lines.mapped('wilco_amount_net_profit'))
            project.wilco_project_pnl = total_net_profit

            total_revenue = sum(analytic_lines.mapped('wilco_amount_revenue'))
            project.wilco_actual_np_percent = (
                (total_net_profit / total_revenue * 100)
                if total_revenue != 0 else 0.0
            )

            # Calculate cash flow
            total_net_payment = sum(analytic_lines.mapped('wilco_amount_payment_display'))
            project.wilco_actual_cash_flow = total_net_payment
            project.wilco_cash_flow_percent = (
                (total_net_payment / project.wilco_total_invoice_amount * 100)
                if project.wilco_total_invoice_amount != 0 else 0.0
            )

    def wilco_action_view_analytic_lines(self):
        self.ensure_one()
        return {
            'res_model': 'account.analytic.line',
            'type': 'ir.actions.act_window',
            'name': _("Analytic Items"),
            'domain': [('account_id', '=', self.analytic_account_id.id)],
            'views': [(self.env.ref('analytic.view_account_analytic_line_tree').id, 'list'),
                      (self.env.ref('analytic.view_account_analytic_line_form').id, 'form'),
                      (self.env.ref('analytic.view_account_analytic_line_graph').id, 'graph'),
                      (self.env.ref('analytic.view_account_analytic_line_pivot').id, 'pivot')],
            'view_mode': 'tree,form,graph,pivot',
            # 'context': {'search_default_group_date': 1, 'default_account_id': self.analytic_account_id.id}
            'context': {'search_default_partner': 1, 'default_account_id': self.analytic_account_id.id}
        }

    def wilco_project_status_report_listing_print_report_name(self):
        """
        Generate the project status listing report print name with timestamp suffix in format: _YYYYMMDD_HHMMSS
        Returns: 'Project Status Listing - {project_name}_{YYYYMMDD_HHMMSS}'
        """
        from datetime import datetime
        self.ensure_one()
        
        project_name = self.name or 'Project'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f'Project Status Listing - {project_name}_{timestamp}'


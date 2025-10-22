# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class WilcoProjectStatusReportWizard(models.TransientModel):
    _name = 'wilco.project.status.report.wizard'
    _description = 'Project Status Report Wizard'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        help='The project for which to generate the status report'
    )
    
    selected_account_move_id = fields.Many2one(
        'account.move',
        string='Highlight Invoice/Bill',
        domain="[('wilco_project_id', '=', project_id), ('move_type', 'in', ['out_invoice', 'in_invoice'])]",
        help='Select a customer invoice or vendor bill to highlight in the report'
    )
    
    # Section Visibility Options    
    show_quotation = fields.Boolean(
        string='Show Quotation',
        default=True,
        help='Show the Quotations section in the report'
    )
    
    show_sales_order = fields.Boolean(
        string='Show Sales Order',
        default=True,
        help='Show the Sales Orders section in the report'
    )
    
    show_purchase_order = fields.Boolean(
        string='Show Purchase Order',
        default=False,
        help='Show the Purchase Orders section in the report'
    )
    
    show_customer_invoice = fields.Boolean(
        string='Show Customer Invoice',
        default=False,
        help='Show the Customer Invoices section in the report'
    )
    
    show_vendor_bill = fields.Boolean(
        string='Show Vendor Bill',
        default=False,
        help='Show the Vendor Bills section in the report'
    )
    
    show_expense_report = fields.Boolean(
        string='Show Expense Report',
        default=False,
        help='Show the Expense Report section in the report'
    )
    
    show_general_journal = fields.Boolean(
        string='Show General Journal',
        default=False,
        help='Show manually entered journal entries (excluding those from invoices/bills/payments)'
    )

    all_vendor_bills = fields.Many2many(
        'account.move',
        string='All Vendor Bills',
        compute='_compute_all_vendor_bills',
        help='All vendor bills related to this project (direct or via analytic lines)'
    )
    
    expense_report_bills = fields.Many2many(
        'account.move',
        string='Expense Report Bills',
        compute='_compute_expense_report_bills',
        help='Vendor bills linked to expense reports for this project'
    )
    
    manual_journal_entries = fields.Many2many(
        'account.move',
        string='Manual Journal Entries',
        compute='_compute_manual_journal_entries',
        help='Manually entered journal entries for this project'
    )
    
    @api.depends('project_id', 'show_vendor_bill', 'show_expense_report')
    def _compute_all_vendor_bills(self):
        """
        Compute all vendor bills related to the project (excluding expense report bills):
        1. Bills with direct project_id link
        2. Bills without project_id but with invoice lines having analytic distribution matching this project
        Excludes bills that are linked to expense reports.
        """
        for wizard in self:
            if not wizard.project_id or not wizard.show_vendor_bill:
                wizard.all_vendor_bills = self.env['account.move']
                continue
            
            # Get bills with direct project_id link (excluding expense report bills)
            bills_with_project = self.env['account.move'].search([
                ('wilco_project_id', '=', wizard.project_id.id),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', '=', 'posted'),
                ('expense_sheet_id', '=', False)  # Exclude expense report bills
            ], order='invoice_date desc, name desc')
            
            # Get the analytic account string for comparison
            analytic_account_str = str(wizard.project_id.analytic_account_id.id)
            
            # Get bills without project_id but with matching analytic lines (excluding expense report bills)
            bills_no_project = self.env['account.move'].search([
                ('wilco_project_id', '=', False),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', '=', 'posted'),
                ('expense_sheet_id', '=', False)  # Exclude expense report bills
            ], order='invoice_date desc, name desc')
            
            # Filter bills that have at least one line with matching analytic distribution
            bills_with_analytic = self.env['account.move']
            for bill in bills_no_project:
                for line in bill.invoice_line_ids:
                    if line.analytic_distribution and analytic_account_str in line.analytic_distribution:
                        bills_with_analytic |= bill
                        break  # Found a matching line, no need to check more lines
            
            # Combine both recordsets (union automatically removes duplicates)
            wizard.all_vendor_bills = bills_with_project | bills_with_analytic

    @api.depends('project_id', 'show_expense_report')
    def _compute_expense_report_bills(self):
        """
        Compute vendor bills linked to expense reports for the project:
        1. Bills with direct project_id link and expense_sheet_id
        2. Bills without project_id but with invoice lines having analytic distribution matching this project and expense_sheet_id
        """
        for wizard in self:
            if not wizard.project_id or not wizard.show_expense_report:
                wizard.expense_report_bills = self.env['account.move']
                continue
            
            # Get bills with direct project_id link and linked to expense reports
            bills_with_project = self.env['account.move'].search([
                ('wilco_project_id', '=', wizard.project_id.id),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', '=', 'posted'),
                ('expense_sheet_id', '!=', False)  # Only expense report bills
            ], order='invoice_date desc, name desc')
            
            # Get the analytic account string for comparison
            analytic_account_str = str(wizard.project_id.analytic_account_id.id)
            
            # Get bills without project_id but with matching analytic lines and linked to expense reports
            bills_no_project = self.env['account.move'].search([
                ('wilco_project_id', '=', False),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', '=', 'posted'),
                ('expense_sheet_id', '!=', False)  # Only expense report bills
            ], order='invoice_date desc, name desc')
            
            # Filter bills that have at least one line with matching analytic distribution
            bills_with_analytic = self.env['account.move']
            for bill in bills_no_project:
                for line in bill.invoice_line_ids:
                    if line.analytic_distribution and analytic_account_str in line.analytic_distribution:
                        bills_with_analytic |= bill
                        break  # Found a matching line, no need to check more lines
            
            # Combine both recordsets (union automatically removes duplicates)
            wizard.expense_report_bills = bills_with_project | bills_with_analytic

    @api.depends('project_id', 'show_general_journal')
    def _compute_manual_journal_entries(self):
        """
        Compute manual journal entries for the project.
        Only includes moves that are:
        1. Related to the project (either direct project_id or via analytic distribution)
        2. NOT created from invoices, bills, or payments (move_type not in invoice/refund types and not payment moves)
        3. Posted state only
        """
        for wizard in self:
            if not wizard.project_id or not wizard.show_general_journal:
                wizard.manual_journal_entries = self.env['account.move']
                continue
            
            analytic_account_str = str(wizard.project_id.analytic_account_id.id)
            
            # Get all general journal moves (move_type = 'entry') posted
            # These are manually entered entries, not created from invoices/bills/payments
            general_moves = self.env['account.move'].search([
                ('move_type', '=', 'entry'),
                ('state', '=', 'posted'),
                ('journal_id.type', '=', 'general')  # Explicitly filter for general journals
            ], order='date desc, name desc')
            
            manual_entries = self.env['account.move']
            
            for move in general_moves:
                # Check if move has direct project_id
                if move.wilco_project_id and move.wilco_project_id.id == wizard.project_id.id:
                    manual_entries |= move
                # Check if move has lines with matching analytic distribution
                else:
                    for line in move.line_ids:
                        if line.analytic_distribution and analytic_account_str in line.analytic_distribution:
                            manual_entries |= move
                            break  # Found a matching line, no need to check more
            
            wizard.manual_journal_entries = manual_entries

    def wilco_action_print_report(self):
        self.ensure_one()
        
        # Collect project data
        project = self.project_id
        if not project:
            raise ValueError("No project selected for the report.")

        # Return report action
        return self.env.ref('wilco_project.action_report_project_status').report_action(self)

    def report_print_name(self):
        """
        Generate the report print name with timestamp suffix in format: _YYYYMMDD_HHMMSS
        Returns: 'Project Status - {project_name}_{YYYYMMDD_HHMMSS}'
        """
        from datetime import datetime
        self.ensure_one()
        
        project_name = self.project_id.name or 'Project'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f'Project Status - {project_name}_{timestamp}'

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
    
    all_vendor_bills = fields.Many2many(
        'account.move',
        string='All Vendor Bills',
        compute='_compute_all_vendor_bills',
        help='All vendor bills related to this project (direct or via analytic lines)'
    )

    @api.depends('project_id', 'show_vendor_bill')
    def _compute_all_vendor_bills(self):
        """
        Compute all vendor bills related to the project:
        1. Bills with direct project_id link
        2. Bills without project_id but with invoice lines having analytic distribution matching this project
        """
        for wizard in self:
            if not wizard.project_id or not wizard.show_vendor_bill:
                wizard.all_vendor_bills = self.env['account.move']
                continue
            
            # Get bills with direct project_id link
            bills_with_project = self.env['account.move'].search([
                ('wilco_project_id', '=', wizard.project_id.id),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', '=', 'posted')
            ], order='invoice_date desc, name desc')
            
            # Get the analytic account string for comparison
            analytic_account_str = str(wizard.project_id.analytic_account_id.id)
            
            # Get bills without project_id but with matching analytic lines
            bills_no_project = self.env['account.move'].search([
                ('wilco_project_id', '=', False),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', '=', 'posted')
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

    def wilco_action_print_report(self):
        self.ensure_one()
        
        # Collect project data
        project = self.project_id
        if not project:
            raise ValueError("No project selected for the report.")

        # Return report action
        return self.env.ref('wilco_project.action_report_project_status').report_action(self)

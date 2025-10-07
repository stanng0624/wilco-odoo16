# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class WilcoProjectStatusReportWizard(models.TransientModel):
    """
    Wizard for generating Project Status Report.
    
    This wizard collects all financial transactions related to a project
    and generates a comprehensive status report showing:
    - Sales orders linked to the project
    - Customer invoices linked to the project
    - Vendor bills linked to the project
    """
    _name = 'wilco.project.status.report.wizard'
    _description = 'Project Status Report Wizard'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        help='The project for which to generate the status report'
    )

    def wilco_action_print_report(self):
        """
        Generate and display the project status report.
        
        Collects all related transactions and returns the report action.
        """
        self.ensure_one()
        
        # Collect project data
        project = self.project_id
        
        # Collect sales orders linked to this project via wilco_project_id
        sales_orders = self.env['sale.order'].search([
            ('wilco_project_id', '=', project.id)
        ], order='date_order desc, name desc')
        
        _logger.info(f"Found {len(sales_orders)} sales orders for project {project.name}")
        
        # Collect customer invoices linked to this project via wilco_project_id
        customer_invoices = self.env['account.move'].search([
            ('wilco_project_id', '=', project.id),
            ('move_type', '=', 'out_invoice')
        ], order='invoice_date desc, name desc')

        _logger.info(f"Found {len(customer_invoices)} customer invoices for project {project.name}")
        
        # Collect vendor bills linked to this project via wilco_project_id
        vendor_bills = self.env['account.move'].search([
            ('wilco_project_id', '=', project.id),
            ('move_type', '=', 'in_invoice')
        ], order='invoice_date desc, name desc')
        
        _logger.info(f"Found {len(vendor_bills)} vendor bills for project {project.name}")
        
        # Return report action
        return self.env.ref('wilco_project.action_report_project_status').report_action(self)

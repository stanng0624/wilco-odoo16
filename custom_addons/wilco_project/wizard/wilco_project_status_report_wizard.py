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

    def wilco_action_print_report(self):
        self.ensure_one()
        
        # Collect project data
        project = self.project_id
        if not project:
            raise ValueError("No project selected for the report.")

        # Return report action
        return self.env.ref('wilco_project.action_report_project_status').report_action(self)

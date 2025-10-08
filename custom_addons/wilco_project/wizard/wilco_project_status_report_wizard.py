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
    
    selected_customer_invoice_id = fields.Many2one(
        'account.move',
        string='Highlight Customer Invoice',
        domain="[('wilco_project_id', '=', project_id), ('move_type', '=', 'out_invoice')]",
        help='Select a customer invoice to highlight in the report'
    )

    def wilco_action_print_report(self):
        self.ensure_one()
        
        # Collect project data
        project = self.project_id
        if not project:
            raise ValueError("No project selected for the report.")

        # Return report action
        return self.env.ref('wilco_project.action_report_project_status').report_action(self)

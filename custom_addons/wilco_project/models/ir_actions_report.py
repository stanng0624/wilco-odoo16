from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _set_reports_to_html(self, module_name=None):
        """
        Convert reports to HTML format
        
        Args:
            module_name (str, optional): The module name to filter reports. 
                                       If not provided, converts all PDF reports to HTML.
        
        Returns:
            int: Number of reports converted
        """
        domain = [('report_type', '=', 'qweb-pdf')]
        
        if module_name:
            domain.append(('report_name', 'like', f'{module_name}.%'))
            _logger.info(f"Converting reports for module: {module_name}")
        else:
            _logger.info("Converting all PDF reports to HTML format")
            
        reports = self.search(domain)
        converted_count = 0
        
        for report in reports:
            try:
                _logger.info(f"Converting report {report.name} to HTML format")
                report.write({'report_type': 'qweb-html'})
                converted_count += 1
            except Exception as e:
                _logger.error(f"Failed to convert report {report.name}: {str(e)}")
                
        _logger.info(f"Converted {converted_count} reports to HTML format")
        return converted_count 
from odoo import models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class FixSaleOrderLineMissingAccountDistribution(models.TransientModel):
    _name = 'wilco_project.fix_sale_order_line_missing_account_distribution'
    _description = 'Fix Missing Account Distribution for Sales Order Lines'

    def fix_sale_order_line_missing_account_distribution(self, test_run=True):
        """
        Find and fix sales order lines that have wilco_project_id but missing account distribution
        """
        try:
            # Find sales orders with wilco_project_id but lines having no account distribution
            sales_orders = self.env['sale.order'].search([
                ('wilco_project_id', '!=', False),
                ('state', 'not in', ['cancel', 'draft'])
            ])

            fixed_count = 0
            fixed_orders = 0
            for order in sales_orders:
                # Find order lines with missing account distribution
                lines_to_fix = order.order_line.filtered(
                    lambda l: not l.analytic_distribution
                )
                
                if not lines_to_fix:
                    continue

                if not test_run:
                    lines_to_fix.write({
                        'analytic_distribution': {
                            str(order.wilco_project_id.analytic_account_id.id): 100
                        }
                    })
                
                fixed_count += len(lines_to_fix)
                fixed_orders += 1
                _logger.info(f"{'Would update' if test_run else 'Updated'} account distribution for {len(lines_to_fix)} lines in sale order {order.name}")

            summary_message = f"""
Account Distribution Fix Summary:
--------------------------------
Total Orders {'To Be' if test_run else ''} Fixed: {fixed_orders}
Total Lines {'To Be' if test_run else ''} Fixed: {fixed_count}
{'(TEST RUN - No changes made)' if test_run else ''}
--------------------------------
            """
            _logger.info(summary_message)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Account Distribution Fix Complete'),
                    'message': summary_message.strip(),
                    'type': 'success',
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'}
                }
            }

        except Exception as e:
            _logger.error(f"Error during account distribution fix: {str(e)}")
            raise UserError(_("Error during account distribution fix: %s") % str(e))
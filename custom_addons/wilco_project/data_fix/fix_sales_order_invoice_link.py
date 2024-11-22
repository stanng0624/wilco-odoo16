
import logging
from odoo import models, fields, api
from odoo.fields import Command

_logger = logging.getLogger(__name__)

class FixSalesOrderInvoiceLink(models.AbstractModel):
    _name = 'data_fix.fix_sales_order_invoice_link'
    _description = 'Fix Sales Order and Invoice Linkage'

    @api.model
    def fix_sales_order_invoice_link(self, test_run=True):
        offset = 0
        i = 0
        j = 0
        # Only consider invoices with a wilco_project_id
        domain = [
            ('wilco_project_id', '!=', False),
            # ('wilco_project_id.name', '=', 'WC-M23298'),
            ('state', '=', 'posted'),  # Only consider customer invoices
            ('move_type', '=', 'out_invoice'),  # Only consider customer invoices
            # ('name', '=', 'INV/2024/00228')
        ]

        #invoices = self.env['account.move'].search(domain, offset=offset, limit=batch_size)
        invoices = self.env['account.move'].search(domain)

        for invoice in invoices:
            try:
                # Ensure the invoice has a wilco_project_id
                if not invoice.wilco_project_id:
                    _logger.warning(f"Invoice {invoice.name} is missing wilco_project_id. Skipping.")
                    continue

                invoice_sale_line_ids = invoice.line_ids.sale_line_ids
                invoice_sale_order = invoice_sale_line_ids.mapped('order_id')
                # Find the related sales order using invoice_origin
                sales_order = self.env['sale.order'].search([
                    ('wilco_project_id', '=', invoice.wilco_project_id.id)
                ], limit=1)

                if sales_order and invoice_sale_order:
                    if sales_order.wilco_project_id != invoice_sale_order.wilco_project_id:
                        _logger.warning(
                            f"Invoice SO {invoice.name} {invoice.wilco_project_id.name} and Sales Order {invoice_sale_order.name} {invoice_sale_order.wilco_project_id.name} have difference."
                        )
                        if not test_run:
                            j = j + 1

                elif not invoice_sale_order and sales_order:
                    _logger.warning(
                        f"Invoice SO {invoice.name} {invoice.wilco_project_id.name} no SO and Sales Order {sales_order.name} {sales_order.wilco_project_id.name} exist."
                    )
                    invoice_lines = invoice.line_ids
                    # first_invoice_line = invoice_lines.filtered(lambda x: not x.display_type and not x.is_downpayment)[:1]
                    first_invoice_line = invoice_lines[:1]
                    sales_order_lines = sales_order.order_line
                    first_sales_line = sales_order_lines.filtered(lambda x: not x.display_type and not x.is_downpayment)[:1]

                    if not first_invoice_line:
                        _logger.warning('No valid invoice line is found. Skippng')
                        continue
                    if not first_sales_line:
                        _logger.warning('No valid sales line is found. Skippng')
                        continue

                    if first_invoice_line.sale_line_ids:
                        continue

                    if not test_run:
                        first_invoice_line.write({
                            'sale_line_ids': [Command.link(first_sales_line.id)]
                        })

                        _logger.warning(
                            f"Invoice SO {invoice.name} {invoice.wilco_project_id.name} is linked to Sales Order {sales_order.name} {sales_order.wilco_project_id.name}."
                        )

                        j = j + 1

                elif not sales_order and invoice_sale_order:
                    _logger.warning(
                        f"Invoice SO {invoice.name} {invoice_sale_order.wilco_project_id.name} has SO {invoice_sale_order.name} and No Sales Order {invoice.wilco_project_id.name} exist."
                    )
                else:
                    _logger.warning(
                        f"Invoice {invoice.name} {invoice.wilco_project_id.name} has no matching sales order and no linked SO"
                    )
                    continue

                i = i + 1

            except Exception as e:
                _logger.error(f"Error processing Invoice {invoice.name}: {str(e)}")

        _logger.warning(
            f"No of record: {i}"
            f"No of record fixed: {j}"
        )
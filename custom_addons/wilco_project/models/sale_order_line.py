from odoo import models, fields, api, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):

        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)

        if self.order_id.wilco_invoice_method == 'single_line' and not self.display_type and not self.is_downpayment:
            values = self._set_invoice_line_for_single_line(values)

        return values

    def _set_invoice_line_for_single_line(self, values):
        sale_order = self.order_id
        invoices = sale_order.invoice_ids

        values['name'] = _('Invoice from order: {}').format(sale_order.display_name)
        values['quantity'] = 1
        values['discount'] = 0

        # down_payment_lines = sale_order.order_line.filtered(lambda line:
        #                                               line.is_downpayment
        #                                               and not line.display_type
        #                                               and not line._get_downpayment_state()
        #                                               )
        # down_payment_lines_deducted = invoices.line_ids.filtered(lambda line:
        #                                               line.quantity < 0
        #                                               and line.is_downpayment
        #                                               )

        # amount_downpayment = sum(down_payment_lines.mapped("price_unit"))
        # amount_downpayment_deducted = sum(down_payment_lines_deducted.mapped("price_unit"))
        # amount_ordered_total = sale_order.amount_total
        # amount_invoiced_total = sum(invoices.mapped("amount_total"))
        # amount_invoiced_total = sale_order.wilco_amount_invoiced_total - sale_order.wilco_amount_downpayment_deducted
        # amount_invoice_remain = amount_ordered_total - amount_invoiced_total

        # values['price_unit'] = amount_invoice_remain if amount_invoice_remain > 0 else 0
        values['price_unit'] = sale_order.wilco_amount_invoice_remainder

        analytic_account_id = sale_order.analytic_account_id.id
        if analytic_account_id:
            analytic_account_id = str(analytic_account_id)
            values['analytic_distribution'] = {analytic_account_id: 100}

        return values
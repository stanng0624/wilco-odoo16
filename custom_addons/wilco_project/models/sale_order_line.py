from odoo import models, fields, api, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):

        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)

        if self.order_id.wilco_invoice_method == 'invoice_by_order' and not self.display_type and not self.is_downpayment:
            values = self._set_invoice_line_for_invoice_by_order(values)

        return values

    def _set_invoice_line_for_invoice_by_order(self, values):
        sale_order = self.order_id

        order_ref = sale_order.wilco_document_number if sale_order.wilco_document_number else sale_order.name
        values['name'] = _('Bill to Order: {}').format(order_ref)
        values['quantity'] = 1
        values['discount'] = 0
        values['price_unit'] = sale_order.wilco_amount_invoice_remainder

        analytic_account_id = sale_order.analytic_account_id.id
        if analytic_account_id:
            analytic_account_id = str(analytic_account_id)
            values['analytic_distribution'] = {analytic_account_id: 100}

        return values
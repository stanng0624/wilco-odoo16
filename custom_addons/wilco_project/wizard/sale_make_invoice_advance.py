from odoo import api, fields, models

INVOICE_METHOD = [
    ('invoice_by_line', 'Invoice By Order Line'),
    ('invoice_by_order', 'Invoice By Order Total')
]

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    wilco_invoice_method = fields.Selection(
        selection=INVOICE_METHOD,
        string="Invoice Mehtod",
        default='invoice_by_order')

    def _create_invoices(self, sale_orders):
        self.ensure_one()
        sale_orders.write({'wilco_invoice_method': self.wilco_invoice_method})

        return super(SaleAdvancePaymentInv, self)._create_invoices(sale_orders)
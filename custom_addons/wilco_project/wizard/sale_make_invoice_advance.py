from odoo import api, fields, models

INVOICE_METHOD = [
    ('invoice_per_line', 'Invoice Per Order Line'),
    ('single_line', 'Singe Line')
]

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    wilco_invoice_method = fields.Selection(
        selection=INVOICE_METHOD,
        string="Invoice Mehtod",
        default='single_line')

    def _create_invoices(self, sale_orders):
        self.ensure_one()
        sale_orders.write({'wilco_invoice_method': self.wilco_invoice_method})

        return super(SaleAdvancePaymentInv, self)._create_invoices(sale_orders)
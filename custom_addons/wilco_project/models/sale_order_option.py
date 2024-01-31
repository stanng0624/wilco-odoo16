from odoo import models, fields, api, _

class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'

    wilco_line_ref = fields.Char(string='Line reference')
    wilco_price_subtotal = fields.Float(
        string="Subtotal",
        compute='_compute_amount',
        store=True, precompute=True)

    @api.depends('quantity', 'discount', 'price_unit')
    def _compute_amount(self):
        """
        Compute the amounts of the SO Option line.
        """
        for line in self:
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            # amount_tax = totals['amount_tax']
            line.update({'wilco_price_subtotal': amount_untaxed})

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            price_unit=self.price_unit,
            quantity=self.quantity,
            discount=self.discount,
            price_subtotal=self.wilco_price_subtotal,
        )

    @api.depends('line_id', 'order_id.order_line', 'product_id')
    def _compute_is_present(self):
        option_id_computed = []
        for option in self:
            if option.line_id:
                option.is_present = True
            else:
                option.is_present = False #Always allow add optional item first
            option_id_computed.append(option.id)

        option_computed = self.filtered(lambda r: r.id in option_id_computed)
        super(SaleOrderOption, self - option_computed)._compute_is_present()

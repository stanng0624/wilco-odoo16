from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    wilco_sale_skip_update_name = fields.Boolean(string="Skip update description of sales order line")
    wilco_sale_skip_update_price_unit = fields.Boolean(string="Skip update unit price of sales order line")
    wilco_sale_skip_update_qty = fields.Boolean(string="Skip update quantity of sales order line")
    wilco_sale_skip_update_product_uom = fields.Boolean(string="Skip update UoM of sales order line")
    wilco_purchase_skip_update_name = fields.Boolean(string="Skip update description of purchase order line")
    wilco_purchase_skip_update_price_unit = fields.Boolean(string="Skip update unit price of purchase order line")
    wilco_purchase_skip_update_qty = fields.Boolean(string="Skip update quantity of purchase order line")
    wilco_purchase_skip_update_product_uom = fields.Boolean(string="Skip update UoM of purchase order line")

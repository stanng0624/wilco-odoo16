from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    wilco_sale_skip_update_name = fields.Boolean(string="Skip update description of sales order line")
    wilco_purchase_skip_update_name = fields.Boolean(string="Skip update description of purchase order line")

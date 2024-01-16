from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    wilco_sale_skip_update_name = fields.Boolean(string="Skip update description of order line")

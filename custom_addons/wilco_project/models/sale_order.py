from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wilco_remark = fields.Text(string='Addtional remarks')
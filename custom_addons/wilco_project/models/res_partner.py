from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ref = fields.Char(string='Our reference')

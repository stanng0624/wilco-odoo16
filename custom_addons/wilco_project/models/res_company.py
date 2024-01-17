from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    wilco_signature = fields.Binary(string='Signature',
                                    help='Attach the signature here')

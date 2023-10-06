from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wilco_order_header = fields.Text(string='Quotation/Order header')
    wilco_our_reference = fields.Text(string='Our reference')
    wilco_contact_info = fields.Text(string='Contact information')
    wilco_revision_no = fields.Integer(string='Revision no.', default=0)
    wilco_revision_date = fields.Date(string='Revision date')
    wilco_document_number = fields.Text(string='Document number', compute='_wilco_compute_document_name')
    wilco_remark = fields.Text(string='Additional remarks')

    @api.onchange('wilco_revision_no')
    def onchange_wilco_revision_no(self):
        if self.wilco_revision_no == 0:
            self.wilco_revision_date = ""
        else:
            self.wilco_revision_date = fields.datetime.today()

    def _wilco_compute_document_name(self):
        for saleOrder in self:
            name = ""
            if saleOrder.wilco_revision_no > 0:
                name = f"{saleOrder.name}-R{saleOrder.wilco_revision_no}"
            else:
                name = saleOrder.name
            saleOrder.wilco_document_number = name

from odoo import api, fields, models
from odoo.tools.mail import is_html_empty


class ResCompany(models.Model):
    _inherit = 'res.company'

    wilco_signature = fields.Binary(string='Signature',
                                    help='Attach the signature here')

    wilco_sale_terms = fields.Html(string='Default Terms and Conditions (Quotation/Order)', translate=True)
    wilco_sale_terms_type = fields.Selection([('plain', 'Add a Note'), ('html', 'Add a link to a Web Page')],
                                            string='Terms & Conditions format (Quotation/Order)', default='plain')
    wilco_sale_terms_html = fields.Html(string='Default Terms and Conditions as a Web page (Quotation/Order)', translate=True,
                                         sanitize_attributes=False,
                                         compute='_wilco_compute_sale_terms_html', store=True, readonly=False)

    @api.depends('wilco_sale_terms_type')
    def _wilco_compute_sale_terms_html(self):
        for company in self.filtered(
                lambda company: is_html_empty(company.wilco_sale_terms_html) and company.wilco_sale_terms_type == 'html'):
            html = self.env['ir.qweb']._render('account.account_default_terms_and_conditions',
                                               {'company_name': company.name,
                                                'company_country': company.country_id.name},
                                               raise_if_not_found=False)
            if html:
                company.wilco_sale_terms_html = html

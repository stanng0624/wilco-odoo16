from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wilco_use_sale_terms = fields.Boolean(
        string='Default Terms & Conditions (Quotation/Order)',
        config_parameter='account.wilco_use_sale_terms')
    wilco_sale_terms = fields.Html(related='company_id.wilco_sale_terms', string="Terms & Conditions (Quotation/Order)", readonly=False)
    wilco_sale_terms_html = fields.Html(related='company_id.wilco_sale_terms_html', string="Terms & Conditions as a Web page (Quotation/Order)",
                                        readonly=False)
    wilco_sale_terms_type = fields.Selection(
        related='company_id.wilco_sale_terms_type', readonly=False)
    wilco_sale_terms_preview_ready = fields.Boolean(string="Display preview button", compute='_wilco_compute_sale_terms_preview')

    @api.depends('wilco_sale_terms_type')
    def _wilco_compute_sale_terms_preview(self):
        for setting in self:
            # We display the preview button only if the terms_type is html in the setting but also on the company
            # to avoid landing on an error page (see terms.py controller)
            setting.wilco_sale_terms_preview_ready = self.env.company.wilco_sale_terms_type == 'html' and setting.wilco_sale_terms_type == 'html'

    #TODO: Terms form for sale term not yet done
    def wilco_action_update_terms(self):
        raise UserError('Quotation/Order terms setup by Web Page not yet done')
        self.ensure_one()
        if hasattr(self, 'website_id') and self.env.user.has_group('website.group_website_designer'):
            return self.env["website"].get_client_action('/terms', True)
        return {
            'name': _('Update Terms & Conditions (Quotation/Order)'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'res.company',
            'view_id': self.env.ref("account.res_company_view_form_terms", False).id,
            'target': 'new',
            'res_id': self.company_id.id,
        }

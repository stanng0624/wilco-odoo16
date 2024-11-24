from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.wilco_project.utils.external_identifier_util import ExternalIdentifierUtil

class ResPartner(models.Model):
    _inherit = 'res.partner'

    ref = fields.Char(string='Our reference')

    @api.constrains('ref')
    def _wilco_check_ref(self):
        for partner in self:
            if not partner.ref:
                continue

            if ' ' in partner.ref:
                raise UserError(_("Our reference cannot contain space."))

            partner_exist_ref = self.env['res.partner'].search([
                ('ref', '=', partner.ref),
                ('id', '!=', self.id),
            ], limit=1)
            if partner_exist_ref:
                raise UserError(_("Our reference '{}' has already been used by another company/individual (Name: {}).").format(
                    partner.ref, partner_exist_ref.display_name))

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)

        for partner in result:
            if partner.ref and not partner._exist_external_identifier():
                partner.write_external_identifier(partner.ref)

        return result

    def write(self, values):
        result = super(ResPartner, self).write(values)

        for partner in self:
            if 'ref' in values:
                if partner.ref:
                    partner.write_external_identifier(partner.ref)
                else:
                    partner._delete_external_identifier()

        return result

    def _exist_external_identifier(self):
        return ExternalIdentifierUtil.exist_external_identifier(
            self.env, 
            self._name, 
            self.id
        )

    def write_external_identifier(self, name):
        return ExternalIdentifierUtil.write_external_identifier(
            self.env, 
            self._name, 
            self.id, 
            name
        )

    def _delete_external_identifier(self):
        existing = self.env['ir.model.data'].search([
            ('model', '=', self._name),
            ('res_id', '=', self.id)
        ], limit=1)
        if existing:
            existing.unlink()
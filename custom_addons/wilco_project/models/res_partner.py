from odoo import api, fields, models
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    ref = fields.Char(string='Our reference')

    @api.constrains('ref')
    def _check_ref(self):
        for partner in self:
            if not partner.ref:
                continue

            if ' ' in partner.ref:
                raise UserError("Our reference cannot contain space.")

            partner_check_exist_ref = self.env['res.partner'].search([
                ('ref', '=', partner.ref),
                ('id', '!=', self.id),
            ], limit=1)
            if partner_check_exist_ref:
                raise UserError("Our reference '{}' has already been used by another company/individual (Name: {}).".format(
                    partner.ref, partner_check_exist_ref.display_name))

    @api.model_create_multi
    def create(self, vals_list):

        result = super().create(vals_list)

        for partner in result:
            if partner.ref:
                partner._wilco_create_external_identifier(partner.ref)

        return result

    def write(self, values):
        result = super(ResPartner, self).write(values)

        for partner in self:
            if partner.ref:
                partner._wilco_write_external_identifier(partner.ref)
            else:
                partner._wilco_delete_external_identifier()

        return result


    def _wilco_exist_external_identifier(self, module = '__import__'):
        self.ensure_one()
        external_identifier = self.env['ir.model.data'].search([
            ('module', '=', module),
            ('model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)

        if external_identifier:
            return True

        return False

    def _wilco_create_external_identifier(
            self,
            external_identifier_name: str,
            module = '__import__'):
        self.ensure_one()
        # Remove space, name is not allowed with space
        external_identifier_name = external_identifier_name.replace(" ","")
        self.env['ir.model.data'].sudo().create({
            'name': external_identifier_name,
            'module': module,
            'model': self._name,
            'res_id': self.id,
            'noupdate': False
        })

    def _wilco_update_external_identifier(
            self,
            external_identifier_name: str,
            module='__import__'):
        self.ensure_one()
        # Remove space, name is not allowed with space
        external_identifier_name = external_identifier_name.replace(" ","")
        external_identifier = self.env['ir.model.data'].search([
            ('module', '=', module),
            ('model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)

        if external_identifier and external_identifier.name != external_identifier_name:
            external_identifier.sudo().write({'name': external_identifier_name})

    def _wilco_write_external_identifier(
            self,
            external_identifier_name: str,
            module='__import__',
            override_existing_id = True):
        self.ensure_one()
        if override_existing_id and self._wilco_exist_external_identifier(module):
            self._wilco_update_external_identifier(external_identifier_name, module)
        else:
            self._wilco_create_external_identifier(external_identifier_name, module)

    def _wilco_delete_external_identifier(
            self,
            module='__import__'):
        self.ensure_one()
        external_identifier = self.env['ir.model.data'].search([
            ('module', '=', module),
            ('model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)

        if external_identifier:
            external_identifier.sudo().unlink()


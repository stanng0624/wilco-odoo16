from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Project(models.Model):
    _inherit = 'project.project'

    name = fields.Char(string='Project Number')
    wilco_project_name = fields.Char(string='Project Name', translate=True)
    wilco_date_award = fields.Date(string='Award Date')

    @api.constrains('name')
    def _check_name(self):
        for project in self:
            if not project.name:
                continue

            if ' ' in project.name:
                raise UserError("Project Number cannot contain space.")

            project_check_exist_name = self.env['project.project'].search([
                ('name', '=', project.name),
                ('id', '!=', self.id),
            ], limit=1)
            if project_check_exist_name:
                raise UserError("Project Number '{}' has already been used by another project (Project Name: {}).".format(
                    project.name, project_check_exist_name.wilco_project_name))

    def name_get(self):
        result = []
        for project in self:
            name = ""
            if project.wilco_project_name:
                name = f"{project.name} {project.wilco_project_name}"
            else:
                name = project.name
            result.append((project.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)

        for project in result:
            if not project.analytic_account_id:
                project._create_analytic_account()

            if not project._wilco_exist_external_identifier():
                project._wilco_create_external_identifier(project.name)

        return result

    def write(self, values):
        if not values.get('analytic_account_id'):
            for project in self:
                if not project.analytic_account_id:
                    project._create_analytic_account()

        result = super(Project, self).write(values) if values else True

        if 'partner_id' in values and self.analytic_account_id:
            projects_read_group = self.env['project.project']._read_group(
                [('analytic_account_id', 'in', self.analytic_account_id.ids)],
                ['analytic_account_id'],
                ['analytic_account_id']
            )
            analytic_account_to_update = self.env['account.analytic.account'].browse([
                result['analytic_account_id'][0]
                for result in projects_read_group
                if result['analytic_account_id'] and result['analytic_account_id_count'] == 1
            ])
            analytic_account_to_update.write({'partner_id': self.partner_id})

        for project in self:
            project._wilco_write_external_identifier(project.name)

        return result

    def wilco_action_view_analytic_account_entries(self):
        self.ensure_one()
        return {
            'res_model': 'account.analytic.line',
            'type': 'ir.actions.act_window',
            'name': _("Gross Margin"),
            'domain': [('account_id', '=', self.analytic_account_id.id)],
            'views': [(self.env.ref('analytic.view_account_analytic_line_tree').id, 'list'),
                      (self.env.ref('analytic.view_account_analytic_line_form').id, 'form'),
                      (self.env.ref('analytic.view_account_analytic_line_graph').id, 'graph'),
                      (self.env.ref('analytic.view_account_analytic_line_pivot').id, 'pivot')],
            'view_mode': 'tree,form,graph,pivot',
            'context': {'search_default_group_date': 1, 'default_account_id': self.analytic_account_id.id}
        }

    def _wilco_exist_external_identifier(self, module = '__import__'):
        self.ensure_one()
        external_identifier = self.env['ir.model.data'].search([
            ('module', '=', module),
            ('res_id', '=', self.id),
            ('model', '=', self._name),
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
            'res_id': self.id,
            'model': self._name,
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
            ('res_id', '=', self.id),
            ('model', '=', self._name),
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


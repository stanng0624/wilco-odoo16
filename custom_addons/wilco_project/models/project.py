from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.wilco_project.utils.external_identifier_util import ExternalIdentifierUtil

class Project(models.Model):
    _inherit = 'project.project'

    name = fields.Char(string='Project Number')
    # Revise 'to_define' label from 'Set Status' to 'No Status'
    last_update_status = fields.Selection(
        selection=[
            ('on_track', 'On Track'),
            ('at_risk', 'At Risk'),
            ('off_track', 'Off Track'),
            ('on_hold', 'On Hold'),
            ('to_define', 'No Status'),
        ])

    wilco_project_name = fields.Char(string='Project Name', translate=True, index=True)
    wilco_date_award = fields.Date(string='Award Date')

    @api.constrains('name')
    def _wilco_check_name(self):
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

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('wilco_project_name', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        # return super()._name_search(name, args, operator, limit, name_get_uid)

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)

        for project in result:
            if not project.analytic_account_id:
                project._create_analytic_account()

            if project.name and not ExternalIdentifierUtil.exist_external_identifier(
                self.env, self._name, project.id):
                ExternalIdentifierUtil.write_external_identifier(
                    self.env, self._name, project.id, project.name)

        return result

    def write(self, values):
        result = super(Project, self).write(values)

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
            if not project.analytic_account_id:
                project._create_analytic_account()

            if 'name' in values and project.name:
                ExternalIdentifierUtil.write_external_identifier(
                    self.env, self._name, project.id, project.name)

        return result

    def wilco_action_view_analytic_lines(self):
        self.ensure_one()
        return {
            'res_model': 'account.analytic.line',
            'type': 'ir.actions.act_window',
            'name': _("Analytic Items"),
            'domain': [('account_id', '=', self.analytic_account_id.id)],
            'views': [(self.env.ref('analytic.view_account_analytic_line_tree').id, 'list'),
                      (self.env.ref('analytic.view_account_analytic_line_form').id, 'form'),
                      (self.env.ref('analytic.view_account_analytic_line_graph').id, 'graph'),
                      (self.env.ref('analytic.view_account_analytic_line_pivot').id, 'pivot')],
            'view_mode': 'tree,form,graph,pivot',
            # 'context': {'search_default_group_date': 1, 'default_account_id': self.analytic_account_id.id}
            'context': {'search_default_partner': 1, 'default_account_id': self.analytic_account_id.id}
        }


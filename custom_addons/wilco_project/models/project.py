from odoo import models, fields, api, _

class Project(models.Model):
    _inherit = 'project.project'

    name = fields.Char(string='Project Number')
    wilco_project_name = fields.Char(string='Project Name', translate=True)
    wilco_date_award = fields.Date(string='Award Date')

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
        """ Create an analytic account if don't provide one
            Note: create it before calling super() to avoid raising the ValidationError from _check_allow_timesheet
        """
        defaults = self.default_get(['analytic_account_id'])
        for vals in vals_list:
            analytic_account_id = vals.get('analytic_account_id', defaults.get('analytic_account_id'))
            if not analytic_account_id:
                analytic_account = self._create_analytic_account_from_values(vals)
                vals['analytic_account_id'] = analytic_account.id
        return super().create(vals_list)

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

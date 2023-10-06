from odoo import models, fields, api

class Project(models.Model):
    _inherit = 'project.project'

    name = fields.Char(string='Project Number')
    wilco_project_name = fields.Char(string='Project Name', required=True, translate=True)

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
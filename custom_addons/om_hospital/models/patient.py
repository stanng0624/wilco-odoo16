# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models, _

class HospitalPatient(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "hospital.patient"
    _description = "Hosiptal Patient"

    name = fields.Char(string='Name', tracking=True)
    date_of_birth = fields.Date(string='Date of birth')
    ref = fields.Char(string='Reference', default='Odoo Mates')
    age = fields.Integer(string='Age', compute='_compute_age')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string='Gender', tracking=True, default='female')
    active = fields.Boolean(string='Active', default=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", copy=False,
                                          ondelete='set null',
                                          domain="[('company_id', '=', False)]",
                                          check_company=True)

    def _compute_company_id(self):
        return self.env.company

    @api.depends('date_of_birth')
    def _compute_age(self):
        print("self......{}".format(self))
        for rec in self:
            rec.age = self.__calc_age(rec)

    def __calc_age(cls, patient) -> int:
        """" Calculate the age from patient record
        """
        today = date.today()
        print("Today: {}".format(today))

        if not patient.date_of_birth:
            return 0

        print("patient.date_of_birth: {}".format(patient.date_of_birth))
        return today.year \
                   - patient.date_of_birth.year \
                   - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))

    def _create_analytic_account(self):
        company = self.env.company
        for patient in self:
            analytic_account = self.env['account.analytic.account'].create({
                'name': patient.name,
                'company_id': company.id,
                'plan_id': company.analytic_plan_id.id,
                'active': True,
            })
            patient.write({'analytic_account_id': analytic_account.id})

    @api.model
    def _create_analytic_account_from_values(self, values):
        company = self.env.company
        name = values.get('name', _('Unknown Analytic Account'))
        analytic_account = self.env['account.analytic.account'].create({
            'name': name,
            'company_id': company.id,
            'plan_id': company.analytic_plan_id.id,
            'active': True,
        })
        return analytic_account

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
            for patient in self:
                if not patient.analytic_account_id:
                    patient._create_analytic_account()
        return super(HospitalPatient, self).write(values)

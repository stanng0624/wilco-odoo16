# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models


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

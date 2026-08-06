# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Division(models.Model):
    _name = 'itsm.division'
    _description = 'Division'

    name = fields.Char(string='Name')
    
    @api.constrains("name")
    def _check_unique_name(self):
        for rec in self:
            if not rec.name:
                continue

            duplicate = self.search([
                ("id", "!=", rec.id),
                ("name", "=", rec.name),
            ], limit=1)

            if duplicate:
                raise ValidationError("Division already exists!")
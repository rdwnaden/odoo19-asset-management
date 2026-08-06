# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Category(models.Model):
    _name = 'itsm.category'
    _description = 'Category'

    name = fields.Char(string='Name')
    icon = fields.Char(string="Icon", default="fa-cube")
    
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
                raise ValidationError("Category already exists!")
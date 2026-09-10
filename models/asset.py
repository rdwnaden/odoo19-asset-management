# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Asset(models.Model):
    _name = 'itsm.asset'
    _inherit = ["mail.thread","mail.activity.mixin"]
    _description = 'Asset'

    name = fields.Char(string='Asset Number', tracking=True)
    category_id = fields.Many2one('itsm.category', string='Category', tracking=True)
    serial_number = fields.Char(string='Serial Number', tracking=True)
    purchase_date = fields.Date('Purchase Date', tracking=True)
    state = fields.Selection([
        ('in_use', 'In Use'),
        ('available', 'Available'),
        ('repair', 'Repair'),
        ('borrowed', 'Borrowed'),
    ], string='Status', tracking=True)
    employee_id = fields.Many2one('itsm.employee', string='Used by', tracking=True)
    division_id = fields.Many2one('itsm.division', string='Division', tracking=True)
    specification = fields.Text('Specification', tracking=True)
    activation_number = fields.Char(string='Activation Number', tracking=True)
    system_model = fields.Char('System Model', tracking=True)
    brand_id = fields.Many2one('itsm.brands', string='Brand', tracking=True)
    location_id = fields.Many2one('itsm.location', string='Location', tracking=True)
    ram = fields.Selection([
        ('4gb', '4GB'),
        ('8gb', '8GB'),
        ('12gb', '12GB'),
        ('16gb', '16GB'),
        ('24gb', '24GB'),
        ('32gb', '32GB'),
        ('64gb', '64GB'),
    ], string='RAM', tracking=True)
    storage_type = fields.Selection([
            ('ssd', 'SSD'),
            ('hdd', 'HDD'),
        ], string='Storage Type', tracking=True)
    storage_size = fields.Selection([
        ('128gb', '128GB'),
        ('256gb', '256GB'),
        ('512gb', '512GB'),
        ('1tb', '1TB'),
        ('2tb', '2TB'),
        ('4tb', '4TB'),
        ('6tb', '6TB'),
        ('8tb', '8TB'),
    ], string='Storage Size', tracking=True)
    antivirus = fields.Boolean('Antivirus', tracking=True)
    antivirus_brand = fields.Text('Antivirus Brands', tracking=True)
    charger = fields.Boolean('Charger', tracking=True)
    mouse = fields.Boolean('Mouse', tracking=True)
    keyboard = fields.Boolean('Keyboard', tracking=True)
    notes = fields.Text('Notes', tracking=True)
    #maintenance_ids = fields.One2many('itsm.maintenance', 'asset_id', string='Maintenance', readonly=True)
    #credential_ids = fields.One2many('itsm.credential', 'asset_id', string='Credentials', readonly=True)
    #used_id = fields.Many2one(string='Used By', related='assign_ids.new_employee_id', readonly=True)
    #location_id = fields.Many2one(string='Location', related='assign_ids.new_location_id', store=True, readonly=True)
    
    def copy(self, default=None):
        default = dict(default or {})

        default["name"] = self.env["ir.sequence"].next_by_code(
            "itsm.asset"
        ) or "/"

        return super().copy(default)
    
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
                raise ValidationError("Asset Number already exists!")
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

    has_ups = fields.Boolean(string="UPS", default=False, tracking=True)
    ups_asset_id = fields.Many2one("itsm.asset", string="UPS Number", tracking=True, domain="[('category_id.name', '=', 'UPS'),('pc_asset_ids', '=', False)]")
    pc_asset_ids = fields.One2many("itsm.asset", "ups_asset_id", string="Used By PC", readonly=True)
    is_pc = fields.Boolean(string="Is PC", compute="_compute_is_pc")
    is_ups = fields.Boolean(string="Is UPS", compute="_compute_is_ups")

    lisence_id = fields.Many2one("itsm.lisence", string="License", tracking=True)
    antivirus_license_id = fields.Many2one("itsm.lisence", string="Antivirus Software", tracking=True, domain="[('category_id.name', '=', 'Antivirus'), ('available_stock', '>', 0)]",)

    @api.onchange("antivirus")
    def _onchange_antivirus(self):
        if not self.antivirus:
            self.antivirus_license_id = False

    @api.constrains("antivirus", "antivirus_license_id")
    def _check_antivirus_license_stock(self):
        for record in self:

            if not record.antivirus and record.antivirus_license_id:
                raise ValidationError(
                    "Antivirus Software harus dikosongkan "
                    "jika Antivirus tidak dicentang."
                )

            if record.antivirus and record.antivirus_license_id:

                license_record = record.antivirus_license_id

                assigned_count = self.search_count([
                    ("antivirus_license_id", "=", license_record.id),
                    ("id", "!=", record.id),
                ])

                if assigned_count >= license_record.stock:
                    raise ValidationError(
                        "License '%s' sudah mencapai batas stock.\n\n"
                        "Stock      : %s\n"
                        "Assigned   : %s\n"
                        "Available  : 0\n\n"
                        "Tidak dapat assign license ini ke asset lain."
                        % (
                            license_record.name,
                            license_record.stock,
                            assigned_count,
                        )
                    )

    @api.depends("category_id")
    def _compute_is_pc(self):
        for record in self:
            record.is_pc = record.category_id.name == "PC"

    @api.depends("category_id")
    def _compute_is_ups(self):
        for record in self:
            record.is_ups = record.category_id.name == "UPS"

    @api.onchange("category_id")
    def _onchange_category_id(self):
        if self.category_id.name != "PC":
            self.has_ups = False
            self.ups_asset_id = False

    @api.constrains("ups_asset_id")
    def _check_ups_assignment(self):
        for record in self:
            if record.ups_asset_id:
                other_pcs = self.search([
                    ("ups_asset_id", "=", record.ups_asset_id.id),
                    ("id", "!=", record.id),
                ])

                if other_pcs:
                    raise ValidationError(
                        "UPS %s sudah digunakan oleh PC %s."
                        % (
                            record.ups_asset_id.name,
                            ", ".join(other_pcs.mapped("name")),
                        )
                    )

    
    
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
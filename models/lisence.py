from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Lisence(models.Model):

    _name = "itsm.lisence"
    _description = "IT Software License"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(string="Name", required=True, tracking=True)
    category_id = fields.Many2one("itsm.category", string="Category", required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    stock = fields.Integer(string="Stock", default=1, tracking=True)
    assigned_count = fields.Integer(string="Assigned",compute="_compute_assigned_count", store=True,)
    available_stock = fields.Integer(string="Available", compute="_compute_assigned_count", store=True,)
    expired_date = fields.Date(string="Expired Date", tracking=True)
    link = fields.Char(string="Login URL", tracking=True)
    active = fields.Boolean(default=True)
    asset_ids = fields.One2many("itsm.asset", "antivirus_license_id", string="Assigned Assets",)
    credential_username = fields.Char(string="Username",tracking=True)
    credential_password = fields.Char(string="Password",encrypted=True)
    days_remaining = fields.Integer(string="Days Remaining", compute="_compute_days_remaining")

    @api.depends("stock", "asset_ids")
    def _compute_assigned_count(self):
        for record in self:
            record.assigned_count = len(record.asset_ids)
            record.available_stock = max(
                record.stock - record.assigned_count,
                0,
            )

    @api.constrains("stock")
    def _check_stock(self):
        for record in self:
            if record.stock < 0:
                raise ValidationError(
                    "Stock license tidak boleh kurang dari 0."
                )

    @api.depends("expired_date")
    def _compute_days_remaining(self):
        today = fields.Date.context_today(self)

        for record in self:
            if record.expired_date:
                record.days_remaining = (
                    record.expired_date - today
                ).days
            else:
                record.days_remaining = 0
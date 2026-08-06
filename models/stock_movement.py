from odoo import models, fields


class AssetStockMovement(models.Model):

    _name = "asset.stock.movement"
    _description = "Stock Movement"
    _order = "date desc"

    item_id = fields.Many2one("asset.stock.item",string="Item",required=True)
    date = fields.Datetime(default=fields.Datetime.now)
    movement_type = fields.Selection(
        [
            ("in", "Stock In"),
            ("out", "Stock Out"),
        ],string="Type",required=True)

    qty = fields.Integer(string="Quantity")
    reference = fields.Char(string="Reference")
    employee_id = fields.Many2one("itsm.employee",string="Employee")
    division_id = fields.Many2one("itsm.division",string="Division")
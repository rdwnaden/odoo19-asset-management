from odoo import models, fields, api, _


class AssetStockItem(models.Model):

    _name = "asset.stock.item"
    _description = "Consumable Stock Item"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _order = "name"

    name = fields.Char(string="Item Name", required=True)
    category_id = fields.Many2one("itsm.category", string="Category", tracking=True)
    description = fields.Text(string="Description", tracking=True)
    qty_available = fields.Integer(string="Available Qty",default=0)
    minimum_stock = fields.Integer(string="Minimum Stock",default=5, tracking=True)
    unit = fields.Selection(
        [
            ('pcs', 'Pieces'),
            ('box', 'Box'),
            ('pack', 'Pack'),
            ('roll', 'Roll'),
            ('set', 'Set'),
        ],
        string="Unit",default="pcs", tracking=True)

    active = fields.Boolean(default=True)
    stock_status = fields.Selection(
        [
            ('normal', 'Normal'),
            ('low', 'Low Stock'),
            ('empty', 'Out of Stock'),

        ],
        compute="_compute_stock_status",string="Status", store=True)

    movement_ids = fields.One2many("asset.stock.movement","item_id",string="Movement History")


    @api.depends("qty_available", "minimum_stock")
    def _compute_stock_status(self):
        for record in self:

            if record.qty_available <= 0:
                record.stock_status = "empty"

            elif record.qty_available < record.minimum_stock:
                record.stock_status = "low"

            else:
                record.stock_status = "normal"
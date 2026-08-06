from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AssetStockReceipt(models.Model):

    _name = "asset.stock.receipt"
    _description = "Stock Receipt"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _order = "date desc"

    name = fields.Char(string="Reference",default="/",readonly=True,copy=False)
    date = fields.Date(string="Date",default=fields.Date.today)
    supplier = fields.Char(string="Supplier")
    line_ids = fields.One2many("asset.stock.receipt.line","receipt_id",string="Items")
    state = fields.Selection(
        [
            ("draft","Draft"),
            ("done","Done")
        ], default="draft")
    

    def action_validate(self):
        for receipt in self:
            if receipt.state == "done":
                raise ValidationError(
                    "Stock Receipt sudah pernah divalidasi."
                )

            for line in receipt.line_ids:
                if line.qty <= 0:
                    raise ValidationError(
                        "Quantity harus lebih dari 0."
                    )

                # Tambah Stock
                line.item_id.qty_available += line.qty

                # Create Movement History
                self.env["asset.stock.movement"].sudo().create({
                    "item_id": line.item_id.id,
                    "movement_type": "in",
                    "qty": line.qty,
                    "reference": receipt.name,
                })
            receipt.state = "done"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = self.env[
                    "ir.sequence"
                ].next_by_code(
                    "asset.stock.receipt"
                ) or "New"

        return super().create(vals_list)

class AssetStockReceiptLine(models.Model):

    _name = "asset.stock.receipt.line"
    _description = "Stock Receipt Line"

    receipt_id = fields.Many2one("asset.stock.receipt", required=True,ondelete="cascade")
    item_id = fields.Many2one("asset.stock.item", string="Item",required=True)
    qty = fields.Integer(string="Quantity",required=True)
    unit = fields.Selection(related="item_id.unit", string="Unit", readonly=True)
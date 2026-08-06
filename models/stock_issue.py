from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AssetStockIssue(models.Model):

    _name = "asset.stock.issue"
    _description = "Stock Issue"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _order = "date desc"

    name = fields.Char(string="Reference",default="/",readonly=True,copy=False)
    date = fields.Date(string="Date", default=fields.Date.today)
    employee_id = fields.Many2one("itsm.employee",string="Employee")
    division_id = fields.Many2one("itsm.division",string="Division")
    line_ids = fields.One2many("asset.stock.issue.line","issue_id",string="Items")
    state = fields.Selection(
        [
            ("draft","Draft"),
            ("done","Done")
        ],default="draft")

    used_by = fields.Selection(
    [
        ("employee", "Employee"),
        ("division", "Division"),
    ],
    string="Used By", default="employee", required=True)

    @api.onchange("used_by")
    def _onchange_used_by(self):

        if self.used_by == "employee":
            self.division_id = False

        else:
            self.employee_id = False


    def action_validate(self):
        for issue in self:
            if issue.state == "done":
                raise ValidationError(
                    "Stock Issue sudah pernah divalidasi."
                )

            for line in issue.line_ids:
                if line.qty <= 0:
                    raise ValidationError(
                        "Quantity harus lebih dari 0."
                    )

                if line.qty > line.item_id.qty_available:
                    raise ValidationError(
                        f"Stock {line.item_id.name} tidak mencukupi. "
                        f"Tersedia: {line.item_id.qty_available}"
                    )

                # Kurangi Stock
                line.item_id.qty_available -= line.qty

                # Buat History Movement
                self.env["asset.stock.movement"].sudo().create({
                    "item_id": line.item_id.id,
                    "movement_type": "out",
                    "qty": line.qty,
                    "reference": issue.name,
                    "employee_id": issue.employee_id.id,
                    "division_id": issue.division_id.id,
                })
            issue.state = "done"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "/":
                vals["name"] = self.env[
                    "ir.sequence"
                ].next_by_code(
                    "asset.stock.issue"
                ) or "/"

        return super().create(vals_list)


class AssetStockIssueLine(models.Model):

    _name = "asset.stock.issue.line"
    _description = "Stock Issue Line"

    issue_id = fields.Many2one("asset.stock.issue",required=True,ondelete="cascade")
    item_id = fields.Many2one("asset.stock.item",string="Item",required=True)
    qty = fields.Integer(string="Quantity",required=True)
    unit = fields.Selection(related="item_id.unit", string="Unit", readonly=True)
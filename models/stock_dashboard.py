from odoo import api, models


class StockDashboard(models.AbstractModel):

    _name = "asset.stock.dashboard"
    _description = "Inventory Dashboard"

    @api.model
    def get_dashboard_data(self):
        Item = self.env["asset.stock.item"]
        total_item = Item.search_count([])
        total_stock = sum(
            Item.search([]).mapped("qty_available")
        )

        low_stock = Item.search_count([
            ("qty_available", "<=", 5),
            ("qty_available", ">", 0),
        ])

        out_stock = Item.search_count([
            ("qty_available", "=", 0),
        ])

        return {
            "total_item": total_item,
            "total_stock": total_stock,
            "low_stock": low_stock,
            "out_stock": out_stock,
        }

    @api.model
    def get_category_data(self):
        Item = self.env["asset.stock.item"]
        categories = {}
        for item in Item.search([]):
            if not item.category_id:
                continue
            category_id = item.category_id.id
            if category_id not in categories:
                categories[category_id] = {
                    "id": category_id,
                    "name": item.category_id.name,
                    "icon": item.category_id.icon or "fa-cube",
                    "count": 0,
                    "qty": 0,
                }
            # jumlah jenis item
            categories[category_id]["count"] += 1
            # total stock pada kategori tersebut
            categories[category_id]["qty"] += item.qty_available
        return list(categories.values())


    @api.model
    def get_low_stock(self):
        items = self.env["asset.stock.item"].search(
            [
                ("qty_available", "<=", 5),
            ],
            limit=10
        )
        result = []

        for item in items:
            result.append({
                "id": item.id,
                "name": item.name,
                "qty": item.qty_available,
                "unit": item.unit,
            })

        return result

    @api.model
    def get_recent_transaction(self):
        movements = self.env[
            "asset.stock.movement"
        ].search(
            [],
            order="create_date desc",
            limit=10,
        )

        result = []

        for move in movements:
            result.append({
                "date": move.create_date,
                "reference": move.reference,
                "item": move.item_id.name,
                "qty": move.qty,
                "unit": move.item_id.unit,
                "employee": move.employee_id.name 
                    if move.employee_id else "",
                "division": move.division_id.name 
                    if move.division_id else "",
                "type": move.movement_type,
            })

        return result
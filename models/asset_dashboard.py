from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class AssetDashboard(models.AbstractModel):
    _name = "asset.dashboard"
    _description = "Asset Dashboard"

    @api.model
    def get_dashboard_data(self):

        Asset = self.env["itsm.asset"]

        # total = Asset.search_count([])
        # assigned = Asset.search_count([("employee_id", "!=", False)])
        # available = Asset.search_count([("employee_id", "=", False)])

        return {
            "total": Asset.search_count([]),
            "in_use": Asset.search_count([("state", "=", "in_use")]),
            "available": Asset.search_count([("state", "=", "available")]),
            "repair": Asset.search_count([("state", "=", "repair")]),
        }


    # @api.model
    # def get_asset_category_data(self):
    #     Asset = self.env["itsm.asset"]
    #     categories = {}

    #     for asset in Asset.search([]):
    #         category = asset.category_id.name or "Undefined"

    #         if category in categories:
    #             categories[category] += 1
    #         else:
    #             categories[category] = 1

    #     return {
    #         "labels": list(categories.keys()),
    #         "values": list(categories.values()),
    #     }

    # @api.model
    # def get_asset_category_data(self):
    #     result = self.env["itsm.asset"].read_group(
    #         [],
    #         ["category_id"],
    #         ["category_id"]
    #     )
    #     categories = []
    #     for r in result:
    #         category = self.env["itsm.category"].browse(
    #             r["category_id"][0]
    #         )

    #         categories.append({
    #             "id": category.id,
    #             "name": category.name,
    #             "icon": category.icon or "fa-cube",
    #             "count": r["category_id_count"],
    #         })
    #         _logger.info("CATEGORY DASHBOARD %s", categories)

    #     return {
    #         "categories": categories
    #     }

    @api.model
    def get_asset_category_data(self):
        Asset = self.env["itsm.asset"]

        result = []

        assets = Asset.search([])

        categories = assets.mapped("category_id")

        for category in categories:

            category_assets = assets.filtered(
                lambda asset: asset.category_id.id == category.id
            )

            in_use = len(category_assets.filtered(
                lambda asset: asset.state == "in_use"
            ))

            available = len(category_assets.filtered(
                lambda asset: asset.state == "available"
            ))

            repair = len(category_assets.filtered(
                lambda asset: asset.state == "repair"
            ))

            result.append({
                "id": category.id,
                "name": category.name,
                "icon": category.icon or "fa-cube",
                "count": len(category_assets),
                "in_use": in_use,
                "available": available,
                "repair": repair,
            })

        return result
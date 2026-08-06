/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class InventoryDashboard extends Component {

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.data = useState({
            // KPI
            total_item: 0,
            total_stock: 0,
            low_stock: 0,
            out_stock: 0,

            // Dynamic
            categories: [],
            low_stock_items: [],
            recent_transactions: [],
        });

        onWillStart(async () => {

            const dashboard = await this.orm.call(
                "asset.stock.dashboard",
                "get_dashboard_data",
                []
            );

            Object.assign(this.data, dashboard);

            this.data.categories = await this.orm.call(
                "asset.stock.dashboard",
                "get_category_data",
                []
            );

            this.data.low_stock_items = await this.orm.call(
                "asset.stock.dashboard",
                "get_low_stock",
                []
            );

            this.data.recent_transactions = await this.orm.call(
                "asset.stock.dashboard",
                "get_recent_transaction",
                []
            );

        });

    }

    openItems(filter = null) {
        let domain = [];

        if (filter === "low_stock") {
            domain = [
                ["qty_available", "<=", 5],
                ["qty_available", ">", 0],
            ];
        }

        if (filter === "out_stock") {
            domain = [
                ["qty_available", "=", 0],
            ];
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Stock Items",
            res_model: "asset.stock.item",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: domain,
        });
    }

    openCategory(categoryId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Stock Items",
            res_model: "asset.stock.item",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: [
                ["category_id", "=", categoryId],
            ],
        });
    }

}

InventoryDashboard.template =
    "asset_management.InventoryDashboard";

registry.category("actions").add(
    "inventory_dashboard",
    InventoryDashboard
);
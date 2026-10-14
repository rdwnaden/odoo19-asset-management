/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AssetDashboard extends Component {

    setup() {

        this.orm = useService("orm");
        this.action = useService("action");

        this.data = useState({
            // KPI Card
            total: 0,
            in_use: 0,
            available: 0,
            repair: 0,
            borrowed: 0,
            damaged: 0,
            disposal: 0,
            sold: 0,

            // Asset By Category
            // category_labels: [],
            // category_values: [],

            categories: [],

            old_purchase_categories: [],
            purchase_date_cutoff: "",

            old_purchase_6_year_categories: [],
            purchase_date_6_year_cutoff: "",

            antivirus_licenses: [],
        });

        this.categoryChart = null;
        this.statusChart = null;

        onWillStart(async () => {
            // Dashboard Cards
            const result = await this.orm.call(
                "asset.dashboard",
                "get_dashboard_data",
                []
            );

            Object.assign(this.data, result);

            // Asset By Category
            // const category = await this.orm.call(
            //     "asset.dashboard",
            //     "get_asset_category_data",
            //     []
            // );

            // this.data.category_labels = category.labels;
            // this.data.category_values = category.values;
            const category = await this.orm.call(
                "asset.dashboard",
                "get_asset_category_data",
                []
            );

            this.data.categories = category;

                        const oldPurchaseData = await this.orm.call(
                "asset.dashboard",
                "get_old_purchase_asset_data",
                []
            );

            this.data.old_purchase_categories =
                oldPurchaseData.categories;

            this.data.purchase_date_cutoff =
                oldPurchaseData.cutoff_date;

            const oldPurchase6YearData = await this.orm.call(
                "asset.dashboard",
                "get_old_purchase_6_year_asset_data",
                []
            );

            this.data.old_purchase_6_year_categories =
                oldPurchase6YearData.categories || [];

            this.data.purchase_date_6_year_cutoff =
                oldPurchase6YearData.cutoff_date || "";


            const antivirusLicenses = await this.orm.call(
                "asset.dashboard",
                "get_antivirus_license_data",
                []
            );

            this.data.antivirus_licenses = antivirusLicenses;

        });

        // onMounted(() => {
        //     setTimeout(() => {
        //         this.renderCategoryChart();
        //         this.renderStatusChart();
        //     }, 300);
        // });

    }


    // old horizontal chart

    // renderCategoryChart() {
    //     const canvas = document.getElementById("assetCategoryChart");
    //     if (!canvas) {
    //         return;
    //     }
    //     // Hindari chart dobel saat dashboard dibuka ulang
    //     if (this.categoryChart) {
    //         this.categoryChart.destroy();
    //     }
    //     this.categoryChart = new Chart(canvas, {
    //         type: "bar",
    //         data: {
    //             labels: this.data.category_labels,
    //             datasets: [{
    //                 label: "Total Asset",
    //                 data: this.data.category_values,
    //                 backgroundColor: [
    //                     "#3B82F6",
    //                     "#10B981",
    //                     "#F59E0B",
    //                     "#EF4444",
    //                     "#8B5CF6",
    //                     "#06B6D4",
    //                     "#EC4899",
    //                     "#84CC16",
    //                 ],
    //                 borderRadius: 8,
    //                 borderSkipped: false,
    //                 barThickness: 22,
    //             }]
    //         },

    //         options: {
    //             indexAxis: "y",        // <-- Horizontal Bar
    //             responsive: true,
    //             maintainAspectRatio: false,
    //             animation: {
    //                 duration: 800,
    //             },
    //             plugins: {
    //                 legend: {
    //                     display: false,
    //                 },
    //                 tooltip: {
    //                     enabled: true,
    //                 },
    //             },

    //             scales: {
    //                 x: {
    //                     beginAtZero: true,
    //                     ticks: {
    //                         precision: 0,
    //                         stepSize: 1,
    //                     },
    //                     grid: {
    //                         color: "#E5E7EB",
    //                     }
    //                 },

    //                 y: {
    //                     grid: {
    //                         display: false,
    //                     }
    //                 }
    //             }
    //         }
    //     });
    // }

    renderStatusChart() {
        const canvas = document.getElementById("assetStatusChart");
        if (!canvas) {
            return;
        }
        if (this.statusChart) {
            this.statusChart.destroy();
        }
        this.statusChart = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: [
                    "In Use",
                    "Available",
                    "Repair",
                    "Borrowed",
                    "damaged",
                    "disposal",
                    "sold",
                ],
                datasets: [{
                    data: [
                        this.data.in_use,
                        this.data.available,
                        this.data.repair,
                        this.data.borrowed,
                        this.data.damaged,
                        this.data.disposal,
                        this.data.sold,
                    ],
                    backgroundColor: [
                        "#22C55E",
                        "#3B82F6",
                        "#F97316",
                        "#F97316",
                        "#F97316",
                        "#F97316",
                        "#F97316",
                    ],
                    borderWidth: 0,
                    hoverOffset: 10,
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "70%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            usePointStyle: true,
                            pointStyle: "circle",
                            padding: 20,
                        }
                    }
                }
            }
        });
    }
    async openAssets(state = false) {

        let domain = [];

        if (state) {
            domain = [["state", "=", state]];
        }
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Assets",
            res_model: "itsm.asset",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            view_mode: "list,form",
            target: "current",
            domain: domain,
        });
    }

    openCategory(categoryId) {
        this.env.services.action.doAction({
            type: "ir.actions.act_window",
            name: "Assets",
            res_model: "itsm.asset",
            views: [
                [false, "list"],
                [false, "form"]
            ],

            view_mode: "list,form",
            domain: [["category_id", "=", categoryId]],
            target: "current",
        });
    }

    openOldPurchasedCategory(categoryId) {

        const domain = [
            ["purchase_date", "!=", false],
            ["purchase_date", "<", this.data.purchase_date_cutoff],
        ];

        // Filter kategori hanya jika kategori memiliki ID
        if (categoryId) {
            domain.push(["category_id", "=", categoryId]);
        } else {
            domain.push(["category_id", "=", false]);
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Assets Purchased Over 4 Years",
            res_model: "itsm.asset",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            view_mode: "list,form",
            domain: domain,
            target: "current",
        });
    }

    openOldPurchased6YearCategory(categoryId) {
        const domain = [
            ["purchase_date", "!=", false],
            ["purchase_date", "<", this.data.purchase_date_6_year_cutoff],
        ];

        if (categoryId) {
            domain.push(["category_id", "=", categoryId]);
        } else {
            domain.push(["category_id", "=", false]);
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Assets Purchased Over 6 Years",
            res_model: "itsm.asset",
            views: [[false, "list"], [false, "form"]],
            view_mode: "list,form",
            domain: domain,
            target: "current",
        });
    }

    openAntivirusLicense(licenseId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Antivirus License",
            res_model: "itsm.lisence",
            views: [
                [false, "form"],
            ],
            view_mode: "form",
            res_id: licenseId,
            target: "current",
        });
    }
}

AssetDashboard.template = "asset_management.AssetDashboard";

registry.category("actions").add(
    "asset_dashboard",
    AssetDashboard
);
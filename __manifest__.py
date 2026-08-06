{
    'name': "asset_management",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Ridwan Aden",
    'website': "https://www.port-avant.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail'],

    # always loaded
    'data': [
        'data/sequence.xml',
        'security/ir.model.access.csv',

        'views/asset.xml',
        'views/employee.xml',
        'views/division.xml',
        'views/category.xml',
        'views/brands.xml',
        'views/location.xml',
        'views/dashboard_menu.xml',

        'views/stock_item.xml',
        'views/stock_receipt.xml',
        'views/stock_issue.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
    'web.assets_backend': [
        'asset_management/static/src/dashboard/dashboard.js',
        'asset_management/static/src/dashboard/dashboard.xml',
        'asset_management/static/src/dashboard/dashboard.scss',
        'asset_management/static/lib/Chart/chart.umd.js',

        "asset_management/static/src/dashboard/inventory_dashboard.js",
        # "asset_management/static/src/dashboard/inventory_dashboard.scss",
        "asset_management/static/src/dashboard/inventory_dashboard.xml",
        ],
    },
}


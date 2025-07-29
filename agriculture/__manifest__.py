{
    'name': 'Agriculture CC',
    'version': '1.2',
    'category': 'Agriculture/Agriculture',
    'summary': 'custom agri',
    'depends': [
        'base', 'stock', 'mrp', 'account', 'mail',
    ],
    'data': [
        'security/user_group.xml',
        'security/company_rule.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/agriculture_views.xml',
        'views/product_views.xml',
        'views/configuration_views.xml',
        'views/reporting_views.xml',
        'views/agriculture_menus.xml',
        'views/product_inherit_views.xml',
        'report/report_planting.xml',
        'report/report_input.xml',

    ],
    "application": "True",

    'license': 'LGPL-3',
}

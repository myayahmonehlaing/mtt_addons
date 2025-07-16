{
    'name': 'Custom Consignment',
    'version': '1.0',
    'depends': ['base', 'sale', 'mail', 'stock', 'report_xlsx'],
    'author': 'ChocoMoco',
    'category': 'Sales',
    'summary': '',
    'data': [
        'security/company_rule.xml',
        'views/res_config_settings_views.xml',
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/consignment_views.xml',
        'views/sale_order_views.xml',
        'report/consignment_xlsx_report.xml',
        'views/consignment_wizard_views.xml',
        'views/consignment_menus.xml',
        'report/consignment_reports.xml',
        'report/consignment_pdf_report.xml',

    ],
    'installable': True,
    'application': False,
}

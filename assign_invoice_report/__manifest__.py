{
    'name': 'Custom Invoice Report',
    'version': '1.0',
    'depends': ['base', 'sale', 'account'],
    'author': 'ChocoMoco',
    'category': 'Accounting',
    'summary': 'Add department field to Sales Order',
    'data': [
        # 'views/report_invoice_field.xml',
        'views/report_invoice_custom.xml',
        'views/report_discount_invoice.xml',

    ],
    'installable': True,
    'application': False,
}

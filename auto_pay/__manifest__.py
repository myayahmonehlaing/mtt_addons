{
    'name': 'Auto Pay Button',
    'version': '1.0',
    'depends': ['base','sale','stock','account','sale_management'],
    'author': 'ChocoMoco',
    'category': 'Sales',
    'summary': 'Add picking state done and invoice create',
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/payment_wizard_views.xml',

    ],
    'installable': True,
    'application': False,
}
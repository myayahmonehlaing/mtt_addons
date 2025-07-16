{
    'name': 'Custom Department Group',
    'version': '1.0',
    'depends': ['base','sale','hr','account'],
    'author': 'ChocoMoco',
    'category': 'Sales',
    'summary': 'Add department field to Sales Order',
    'data': [
        'views/sale_order_view_form.xml',
    ],
    'installable': True,
    'application': False,
}
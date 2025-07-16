{
    'name': 'Custom Security Group',
    'version': '1.0',
    'depends': ['base', 'account', 'account_accountant', 'sale', 'hr', 'product'],
    'author': 'ChocoMoco',
    'category': 'Accounting',
    'summary': 'Add department field to Sales Order',
    'data': [
        'security/accounting_group.xml',
        'security/ir.model.access.xml',
        'security/accounting_group_rule.xml',
        'security/sales_group.xml',
        'views/account_override.xml',

    ],
    'installable': True,
    'application': False,
}

# -*- coding: utf-8 -*-

{
    'name': 'Wilco - Project Management',
    'version': '1.0.0',
    'category': 'Wilco',
    'author': 'Stan Ng',
    'sequence': -100,
    'summary': 'Wilco Project Management',
    'description': """
This module contains all the common features of Hospital management
    """,
    'depends': ['base','sale','project','purchase','account','om_account_budget'],
    'data': [
        'views/res_partner_views_inherit.xml',
        'views/project_views_inherit.xml',
        'views/sale_order_views_inherit.xml',
        'report/sale_report_inherit.xml',
        'views/purchase_views_inherit.xml',
        'report/purchase_report_inherit.xml',
        'views/account_move_views_inherit.xml',
        'report/report_invoice_inherit.xml',
        'views/analytic_account_views_inherit.xml',
        'views/account_analytic_account_views_inherit.xml',
        'wizard/sale_make_invoice_advance_views_inherit.xml',
        'report/report_payment_receipt_template_inherit.xml',
        'report/external_layout_boxed_inherit.xml',
    ],
    'demo': [],
    'application': True,
    'auto_install': False,
    'assets': {},
    'license': 'LGPL-3',
}

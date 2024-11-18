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
    'depends': ['base','web','sale','project','purchase','account','om_account_budget'],
    'data': [
        'views/res_partner_views_inherit.xml',
        'views/project_views_inherit.xml',
        'views/sale_order_views_inherit.xml',
        'views/purchase_views_inherit.xml',
        'views/account_analytic_account_views_inherit.xml',
        'views/analytic_line_views_inherit.xml',
        'views/account_move_views_inherit.xml',
        'views/account_payment_views_inherit.xml',
        'views/analytic_account_views_inherit.xml',
        'views/analytic_line_views_inherit.xml',
        'views/product_views_inherit.xml',
        'views/res_company_views_inherit.xml',
        'views/res_config_settings_views_inherit.xml',
        'views/webclient_templates_inherit.xml',
        'report/sale_report_template.xml',
        'report/sale_report_inherit.xml',
        'report/sale_report_views.xml',
        'report/purchase_report_template.xml',
        'report/purchase_report_inherit.xml',
        'report/purchase_report_views.xml',
        'report/invoice_report_inherit.xml',
        'report/payment_receipt_report_inherit.xml',
        'report/signature_template.xml',
        'report/document_reference_template.xml',
        'report/report_template_inherit.xml',
        'wizard/account_payment_register_views_inherit.xml',
        'wizard/sale_make_invoice_advance_views_inherit.xml',
    ],
    'demo': [],
    'application': True,
    'auto_install': False,
    'assets': {},
    'license': 'LGPL-3',
}

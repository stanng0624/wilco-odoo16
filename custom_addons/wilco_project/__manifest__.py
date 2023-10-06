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
    'depends': ['base','sale','project'],
    'data': [
        'views/res_partner_views_inherit.xml',
        'views/sale_order_views_inherit.xml',
        'report/sale_report_inherit.xml',
        'views/project_views_inherit.xml'
    ],
    'demo': [],
    'application': True,
    'auto_install': False,
    'assets': {},
    'license': 'LGPL-3',
}

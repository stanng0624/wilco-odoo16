# Copyright © 2023 Geelani Consultancy & Solutions (https://geelani.com)
# @author: Geelani Consultancy & Solutions (support@geelani.com)
# @author: Aseemuddin Kazi (support@geelani.com)
# @author: Mohammed Sohil Inamdar (support@geelani.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    'name': 'Signature On Sales, Invoice, Purchase',
    'version': '1.0.0',
    'category': '',
    'author': 'Geelani Consultancy and Solutions, Aseemuddin Kazi, Mohamed Sohil Inamdar',
    'website': 'https://www.geelani.com',
    'license': 'LGPL-3',
    'summary': 'Add signature in multiple reports',
    'images': ['static/description/banner.png', 'static/description/icon.png'],
    'depends': ['base', 'account', 'sale', 'purchase'],
    'data': [
        'views/gcs_res_company.xml',
        'views/gcs_invoice.xml',
        'views/gcs_sales.xml',
        'views/gcs_purchase_order.xml',
        'views/gcs_setting.xml',
        'views/gcs_users.xml',
        'reports/gcs_sale_order.xml',
        'reports/gcs_invoice_report.xml',
        'reports/gcs_purchase_order_report.xml',
        'reports/gcs_rfq_report.xml',
    ],
    'support': 'support@geelani.com',
    'application': False,
    'installable': True,
    'auto_install': False,
}

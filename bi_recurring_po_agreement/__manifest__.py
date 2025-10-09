# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name":"Purchase Order Recurring | PO Recurring Agreement",
    "version":"18.0.0.0",
    "category":"Purchase",
    "summary":"Create a Recurring Purchase Order Agreement Make Recurring PO Agreements for Vendor Recurring Orders Request for Quotation Auto-Repeat Purchase Orders Generate Purchase Recurring Agreement for PO Recurring Order Process Advance Purchase Recurring Order",
    "description":"""
        
        Purchase Order Recurring Odoo App helps users to re-generate purchase order agreement based on your demand. User have to configure recurring PO agreement to generates a copy of purchase order based on your given configuration. User have option to select the time interval like day, week and year then select start date, stop date and also select the notify user who will get the email notification about recurring purchase order.

    """,
    "author" : "BROWSEINFO",
    "website": "https://www.browseinfo.com/demo-request?app=bi_recurring_po_agreement&version=18&edition=Community",
    "depends":["base",
               "sale_management",
               "account",
               "purchase",
	          ],
    "data":[
            "security/ir.model.access.csv",
            "security/recurring_menu.xml",
            "data/email_templete.xml",
            "views/res_config_setting_view.xml",
            "views/recurring_purchase_order_views.xml",
            "views/purchase_order_views.xml",
	       ],
    'license':'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://www.browseinfo.com/demo-request?app=bi_recurring_po_agreement&version=18&edition=Community',
    "images":['static/description/Purchase-Order-Recurring-Banner.gif'],
}


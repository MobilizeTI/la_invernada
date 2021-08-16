# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt. Ltd. See LICENSE file for full copyright and licensing details.

{
    'name':'Cash Register On Payments',
    'version':'1.0',
    'category':'Accounting & Finance',
    'price': 80.0,
    'currency': 'EUR',
    'live_test_url': 'https://youtu.be/DAro5koTUUE',
    'summary': 'Cash Register Integration with Customer Invoice and Vendor Bill.',
    'license': 'Other proprietary',
    'description': """
Payment Cash Register:
This module added features on customer/supplier payments to allow account user to link payment with cash register direct through payment menu or customer/supplier invoices register payment option. After selecting and validating payment, module will add cash register line on selected cash register.

User can select cash register through Payments menus.
User can select cash register while they are on customer invoices menu and make payment through select register payment option.
cash register payment
customer payment with cash register
supplier payment with cash register
register payment with cash register
cash register on customer payment
cash register on supplier payment
cash register on payment
payment with cash register
cash on payment
select cash register on payment
select register on payment
select cash note in payment
payment cash register
payment on cash register
register cash
cash register
cash register on payment
cash register payment link
link on cash register
cash register on invoice
invoice cash register
vendor bill cash register
cash register invoices
invoice cash register
If you have customers picking up their orders from your shop and pay at the cash register you will definitely need this little module so you get the entries in the journals. Especially the cash journal. Otherwise all differences will be posted as extraordinary income/loss which is not what you want.
cash payment
cash register payment
customer cash payment
customer pay by cash
cash register on payment
cash book
cash flow
cashflow
cashflow statement
cash flow statement
cash entries
cash journals
cash journal items
cash book journal


            """,
    'author': "Probuse Consulting Service Pvt. Ltd.",
    'website': "http://www.probuse.com",
    'images': ['static/description/345.jpeg'],
    'depends': ['account'],
    'data':[
            'views/payment_cash_register.xml',
            ],
    'installable': True,
    'application': False,
}
 

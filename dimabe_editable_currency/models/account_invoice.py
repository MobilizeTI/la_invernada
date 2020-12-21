from odoo import models, fields, api
import requests
import json


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    exchange_rate = fields.Float(
        'Tasa de Cambio'
    )

    list_references = fields.Many2One('account.invoice.observations')
    list_observations = fields.Many2One('account.invoice.references')

    @api.model
    @api.onchange('date_invoice')
    def _default_exchange_rate(self):
        date = self.date_invoice
        if date:
            currency_id = self.env['res.currency'].search([('name', '=', 'USD')])
            rates = currency_id.rate_ids.search([('name', '=', date)])
            if len(rates) == 0:
                currency_id.get_rate_by_date(date)

            rates = self.env['res.currency.rate'].search([('name', '<=', date)])

            if len(rates) > 0:
                rate = rates[0]
                self.exchange_rate = 1 / rate.rate
        else:
            self.exchange_rate = 0

    def action_invoice_open(self):

        if self.id:
            if self.origin:
                origin = self.env['account.invoice'].search([('number', '=', self.origin)])
                if origin.exchange_rate and (not self.exchange_rate or self.exchange_rate == 0):
                    self.exchange_rate = origin.exchange_rate
            if not self.exchange_rate or self.exchange_rate == 0:
                raise models.ValidationError('debe existir una tasa de cambio')

        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        total = 0
        total_currency = 0
        for line in invoice_move_lines:
            if self.currency_id != company_currency:
                currency = self.currency_id
                date = self._get_currency_rate_date() or fields.Date.context_today(self)
                if not (line.get('currency_id') and line.get('amount_currency')):
                    line['currency_id'] = currency.id
                    line['amount_currency'] = currency.round(line['price'])
                    line['price'] = currency.with_context(
                        optional_usd=self.exchange_rate
                    )._convert(line['price'], company_currency, self.company_id, date)
            else:
                line['currency_id'] = False
                line['amount_currency'] = False
                line['price'] = self.currency_id.round(line['price'])
            if self.type in ('out_invoice', 'in_refund'):
                total += line['price']
                total_currency += line['amount_currency'] or line['price']
                line['price'] = - line['price']
            else:
                total -= line['price']
                total_currency -= line['amount_currency'] or line['price']
        return total, total_currency, invoice_move_lines

    @api.multi
    def send_invoice(self):
        url = 'https://services.dimabe.cl/api/dte/emite'
        productLines = []
        lineNumber = 1
        typeOfExemptEnum = ""
        for item in self.invoice_line_ids:
            haveExempt = False
            #if (len(item.invoice_line_tax_ids) == 0):
            if (len(item.invoice_line_tax_ids) == 0 or (len(item.invoice_line_tax_ids) == 1 and item.invoice_line_tax_ids[0].id == 6)):
                haveExempt = True
                typeOfExemptEnum = item.exempt
            if haveExempt:
                productLines.append(
                    {
                        "LineNumber": str(lineNumber),
                        "ProductTypeCode": "EAN",
                        "ProductCode": str(item.product_id.default_code),
                        "ProductName": item.name,
                        "ProductQuantity": str(int(item.quantity)),
                        "ProductPrice": str(int(item.price_unit)),
                        "ProductDiscountPercent": "0",
                        "DiscountAmount": "0",
                        "Amount": str(int(item.price_subtotal)),
                        "HaveExempt": haveExempt,
                        "TypeOfExemptEnum": typeOfExemptEnum
                    }
                )
            else:
                productLines.append(
                    {
                        "LineNumber": str(lineNumber),
                        "ProductTypeCode": "EAN",
                        "ProductCode": str(item.product_id.default_code),
                        "ProductName": item.name,
                        "ProductQuantity": str(int(item.quantity)),
                        "ProductPrice": str(int(item.price_unit)),
                        "ProductDiscountPercent": "0",
                        "DiscountAmount": "0",
                        "Amount": str(int(item.price_subtotal))
                    }
                )
            lineNumber += 1
        invoice= {
            "createdDate": self.create_date.strftime("%Y-%m-%d"),
            "expirationDate": self.date_due.strftime("%Y-%m-%d"),
            "dteType": self.dte_type_id.code,
            "transmitter": {
                "EnterpriseRut": self.env.user.company_id.invoice_rut,
                "EnterpriseActeco": self.company_activity_id.code,
                "EnterpriseAddressOrigin": self.env.user.company_id.street,
                "EnterpriseCity": self.env.user.company_id.city,
                "EnterpriseCommune": str(self.env.user.company_id.state_id.name),
                "EnterpriseName": self.env.user.company_id.partner_id.name,
                "EnterpriseTurn": self.company_activity_id.name
            },
            "recipient": {
                "EnterpriseRut": self.partner_id.invoice_rut,
                "EnterpriseAddressOrigin": self.partner_id.street,
                "EnterpriseCity": self.partner_id.city,
                "EnterpriseCommune": self.partner_id.state_id.name,
                "EnterpriseName": self.partner_id.name,
                "EnterpriseTurn": self.partner_activity_id.name
            },
            "total": {
                "netAmount": str(int(self.amount_untaxed)),
                "exemptAmount": "0",
                "taxRate": "19",
                "taxtRateAmount": str(int(self.amount_tax)),
                "totalAmount": str(int(self.amount_total))
            },
            "lines": productLines
        }
        raise models.ValidationError(json.dumps(invoice))
        r = requests.post(url, json=invoice)
        #raise models.ValidationError(json.dumps(invoice))
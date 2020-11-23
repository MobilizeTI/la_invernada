from odoo import fields , models , api

class AccountInvoiceXlsx(models.Model):
    _name = 'account.invoice.xlsx'

    report_file = fields.Binary("Libro de Compra")

    report_name = fields.Char("Reporte")

    both = fields.Boolean("Ambas")

    @api.multi
    def generate_book(self):
        for item in self:
            array_worksheet = {}
            company = self.env['res.company'].search([])
import xlsxwriter
from odoo import models


class HrPaySlipXlsx(models.AbstractModel):
    _name = 'report.dimabe_billing_rut.remunerations_book'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        payslip = self.env['hr.payslip'].search([])
        report_name = "Libro de Remuneraciones"
        # One sheet by partner
        indicadores_id = payslip.mapped('indicadores_id').mapped('name')
        sheet = workbook.add_worksheet('Libro de Remuneraciones')
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        sheet.merge_range(
            "B2:E2", "Informe: Libro de Remuneraciones", merge_format)
        sheet.merge_range("B3:E3", "Mes a procesar : {}".format(
            indicadores_id[-1]), merge_format)
        employees = self.env['hr.employee'].search([('address_id', '=', 423)])
        headers = ['Nombre', 'Rut', 'Dias Trabajados', 'Sueldo Base', 'Grat. Legal', 'Horas Extras', 'Bonos Imponibles', 'Aguinaldo Fiestas Patrias', 'Aguinaldo Navidad', 'Horas de Descuento', 'Total Imponible', 'Colacion', 'Movilizacion', 'Asig. Familiar', 'Asig. Varias', 'Total No Imponible',
                  'Total Haberes', 'AFP', 'Salud', 'Seg. Cesantia', 'Impto. Unico', 'Otros AFP', 'Anticipos', 'Anticipo Aguinaldo', 'Credito Social', 'Ahorro AFP', 'Ahorro APV', 'Ahorro CCAF', 'Seg. de Vida CCAF', 'Ptmo. Empresa', 'Retencion Judicial', 'Total Descuentos', 'Liquido A Pagar']
        
        row = 8
        column = 8
        column_head = 6
        for head in headers :
            sheet.write(column_head,8,head)
            column_head += 1
        for employee in employees:
            sheet.merge_range("B{}:D{}".format(row, column),
                              employee.display_name, merge_format)
            sheet.write(0, 0, len(employees))
            sheet.
            row += 1

        bold = workbook.add_format({'bold': True})

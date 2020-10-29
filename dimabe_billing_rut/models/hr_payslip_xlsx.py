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
        merge_format_data = workbook.add_format({
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
        
        
        column_head = 1
        row = 8
        column = 8
        
        for employee in employees:

            if employee.id == employees[0].id:
                sheet.merge_range("A"+str(row - 1)+":"+"D"+str(row - 1),'Nombre:',merge_format)
                sheet.merge_range("E"+str(row - 1)+":"+"F"+str(row - 1),'RUT:',merge_format)
            merge_and_data(sheet,"A"+str(row)+":"+"D"+str(row),employee.display_name,merge_format_data)
            merge_and_data(sheet,"A"+str(row)+":"+"D"+str(row),employee.vat,merge_format_data)
            
            
            row += 1

        bold = workbook.add_format({'bold': True})

    def merge_and_data(self,sheet,to_merge,data,format):
        sheet.merge_range(to_merge,data,merge_format_data)

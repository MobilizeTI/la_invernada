import xlsxwriter
from odoo import models


class HrPaySlipXlsx(models.AbstractModel):
    _name = 'report.dimabe_billing_rut.remunerations_book'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data):
        payslips = self.env['hr.payslip'].search([])
        report_name = "Libro de Remuneraciones"
        # One sheet by partner
        indicadores_id = payslips.mapped('indicadores_id')
        names = indicadores_id.mapped('name')
        sheet = workbook.add_worksheet("Prueba")
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
            names[-1]), merge_format)
        employees = self.env['hr.employee'].search([('address_id', '=', 423)])
        column_head = 1
        row = 8
        column = 8

        for employee in employees:

            if employee.id == employees[0].id:
                sheet.merge_range("A" + str(row - 1) + ":" + "D" +
                                  str(row - 1), 'Nombre:', merge_format)
                sheet.merge_range("E" + str(row - 1) + ":" + "F" +
                                  str(row - 1), 'RUT:', merge_format)
                sheet.merge_range("G" + str(row - 1) + ":" + "H" +
                                  str(row - 1), 'Sueldo Base:', merge_format)
                sheet.merge_range("I" + str(row - 1) + ":" + "J" +
                                  str(row - 1), 'Grat Legal:', merge_format)
                sheet.merge_range("K" + str(row - 1) + ":" + "L" +
                                  str(row - 1), 'Horas Extra:', merge_format)
                sheet.merge_range("M" + str(row - 1) + ":" + "N" +
                                  str(row - 1), 'Bono Imponible:', merge_format)
                if 'Septiembre' in indicadores_id[-1].name:
                    sheet = self.is_september(sheet,row,merge_format)
            sheet.merge_range("A" + str(row) + ":" + "D" + str(row),
                              employee.display_name, merge_format_data)
            sheet.merge_range("E" + str(row) + ":" + "F" + str(row),
                              employee.identification_id, merge_format_data)
            payslip = payslips.filtered(
                lambda a: a.employee_id.id == employee.id and a.indicadores_id.id == indicadores_id[-1].id)
            self.get_values(sheet, "G" + str(row) + ":" + "H" + str(row),
                            'SUELDO BASE', merge_format_data, payslip)
            self.get_values(sheet, "I" + str(row) + ":" + "J" + str(row),
                            'GRATIFICACION LEGAL', merge_format_data, payslip)
            self.get_values(sheet, "K" + str(row) + ":" + "L" + str(row),
                            'HORAS EXTRA ART 32', merge_format_data, payslip)
            self.get_bonus(sheet, "M" + str(row) + ":" + "N" + str(row), merge_format_data, payslip)
            self.get_values(sheet, "O" + str(row) + ":" + "Q" + str(row),
                            'AGUINALDO', merge_format_data, payslip)
            self.get_values(sheet, "R" + str(row) + ":" + "S" + str(row),
                            'AGUINALDO', merge_format_data, payslip)
            self.get_values(sheet, "T" + str(row) + ":" + "U" + str(row),
                            'HORAS DESCUENTO', merge_format_data, payslip)
            self.get_values(sheet, "V" + str(row) + ":" + "W" + str(row),
                            'TOTAL IMPONIBLE', merge_format_data, payslip)
            self.get_values(sheet, "X" + str(row) + ":" + "Y" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "Z" + str(row) + ":" + "AA" + str(row),
                            'MOVILACION', merge_format_data, payslip)
            self.get_values(sheet, "AB" + str(row) + ":" + "AC" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AD" + str(row) + ":" + "AE" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AF" + str(row) + ":" + "AG" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AH" + str(row) + ":" + "AI" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AJ" + str(row) + ":" + "AK" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AL" + str(row) + ":" + "AM" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AN" + str(row) + ":" + "AO" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AP" + str(row) + ":" + "AQ" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AR" + str(row) + ":" + "AS" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AT" + str(row) + ":" + "AU" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AV" + str(row) + ":" + "AW" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AX" + str(row) + ":" + "AY" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AZ" + str(row) + ":" + "BA" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BB" + str(row) + ":" + "BC" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BD" + str(row) + ":" + "BE" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BF" + str(row) + ":" + "BG" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BH" + str(row) + ":" + "BI" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BJ" + str(row) + ":" + "BK" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BL" + str(row) + ":" + "BM" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BN" + str(row) + ":" + "BO" + str(row),
                            'COLACION', merge_format_data, payslip)
            row += 1
        bold = workbook.add_format({'bold': True})

    def get_values(self, sheet, set_in, to_search, format_data, payslip):
        if not payslip.mapped('line_ids').filtered(lambda a: a.name == to_search):
            return sheet.merge_range(set_in,
                                     '',
                                     format_data)
        if len(payslip.mapped('line_ids').filtered(lambda a: a.name == to_search)) > 1:
            return sheet.merge_range(set_in,
                                     payslip.mapped('line_ids').filtered(lambda a: a.name == to_search)[0].total,
                                     format_data)
        else:
            return sheet.merge_range(set_in, payslip.mapped('line_ids').filtered(lambda a: a.name == to_search).total,
                                     format_data)

    def get_bonus(self, sheet, set_in, format_data, payslip):
        return sheet.merge_range(set_in, sum(payslip.mapped('line_ids').filtered(
            lambda a: 'BONO' in a.name and a.category_id.name == 'Imponible').mapped('total')), format_data)

    def is_september(self, sheet,row,merge_format):
        sheet.merge_range("O" + str(row - 1) + ":" + "Q" + str(row - 1),
                          'Aguinaldo Fiestas Pratias:', merge_format)
        sheet.merge_range(
            "R" + str(row - 1) + ":" + "S" + str(row - 1), 'Horas de Descuento:', merge_format)
        sheet.merge_range("T" + str(row - 1) + ":" + "U" +
                          str(row - 1), 'Total Imponible:', merge_format)
        sheet.merge_range("V" + str(row - 1) + ":" + "W" +
                          str(row - 1), 'Colacion', merge_format)
        sheet.merge_range("X" + str(row - 1) + ":" + "Y" +
                          str(row - 1), 'Movilizacion:', merge_format)
        sheet.merge_range("Z" + str(row - 1) + ":" + "AA" +
                          str(row - 1), 'Asig Familiar:', merge_format)
        sheet.merge_range("AB" + str(row - 1) + ":" + "AC" +
                          str(row - 1), 'Asig Varias:', merge_format)
        sheet.merge_range("AD" + str(row - 1) + ":" + "AE" +
                          str(row - 1), 'Total No Imponible:', merge_format)
        sheet.merge_range("AF" + str(row - 1) + ":" + "AG" +
                          str(row - 1), 'Total Haberes:', merge_format)
        sheet.merge_range("AH" + str(row - 1) + ":" + "AI" +
                          str(row - 1), 'AFP:', merge_format)
        sheet.merge_range("AJ" + str(row - 1) + ":" + "AK" +
                          str(row - 1), 'Salud:', merge_format)
        sheet.merge_range("AL" + str(row - 1) + ":" + "AM" +
                          str(row - 1), 'Seg. Cesantia:', merge_format)
        sheet.merge_range("AO" + str(row - 1) + ":" + "AP" +
                          str(row - 1), 'Impto. Unico:', merge_format)
        sheet.merge_range("AQ" + str(row - 1) + ":" + "AR" +
                          str(row - 1), 'Otros AFP:', merge_format)
        sheet.merge_range("AS" + str(row - 1) + ":" + "AT" +
                          str(row - 1), 'Anticipos:', merge_format)
        sheet.merge_range("AU" + str(row - 1) + ":" + "AV" +
                          str(row - 1), 'Anticipo Aguinaldo:', merge_format)
        sheet.merge_range("AW" + str(row - 1) + ":" + "AX" +
                          str(row - 1), 'Credito Social:', merge_format)
        sheet.merge_range("AY" + str(row - 1) + ":" + "AZ" +
                          str(row - 1), 'Ahorro AFP:', merge_format)
        sheet.merge_range("BA" + str(row - 1) + ":" + "BB" +
                          str(row - 1), 'Ahorro APV:', merge_format)
        sheet.merge_range("BC" + str(row - 1) + ":" + "BD" +
                          str(row - 1), 'Ahorro CCAF:', merge_format)
        sheet.merge_range("BE" + str(row - 1) + ":" + "BF" +
                          str(row - 1), 'Seg. de Vida CCAF:', merge_format)
        sheet.merge_range("BG" + str(row - 1) + ":" + "BH" +
                          str(row - 1), 'Ptmo. Empresa:', merge_format)
        sheet.merge_range("BI" + str(row - 1) + ":" + "BJ" +
                          str(row - 1), 'Retencion Judicial:', merge_format)
        sheet.merge_range("BK" + str(row - 1) + ":" + "BL" +
                          str(row - 1), 'Total Descuentos:', merge_format)
        sheet.merge_range("BM" + str(row - 1) + ":" + "BN" +
                          str(row - 1), 'Liquido A Pagar:', merge_format)
        return sheet

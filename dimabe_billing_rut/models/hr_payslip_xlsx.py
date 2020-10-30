import xlsxwriter
from odoo import models


class HrPaySlipXlsx(models.AbstractModel):
    _name = 'report.dimabe_billing_rut.remunerations_book'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
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
                    sheet = self.title_format(sheet,row,merge_format,'Aguinaldo Fiestas Patrias:')
                elif 'Diciembre' in indicadores_id[-1].name:
                    sheet = self.title_format(sheet,row,merge_format,'Aguinaldo Navidad:')
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
            if 'Septiembre' in indicadores_id[-1].name or 'Diciembre' in indicadores_id[-1].name:
                sheet = self.data_format(sheet,row,merge_format,payslip,is_bonus=True)
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

    def title_format(self, sheet,row,merge_format,title):
        sheet.merge_range("O" + str(row - 1) + ":" + "Q" + str(row - 1),
                          title, merge_format)
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
        sheet.merge_range("AN" + str(row - 1) + ":" + "AO" +
                          str(row - 1), 'Impto. Unico:', merge_format)
        sheet.merge_range("AP" + str(row - 1) + ":" + "AQ" +
                          str(row - 1), 'Otros AFP:', merge_format)
        sheet.merge_range("AR" + str(row - 1) + ":" + "AS" +
                          str(row - 1), 'Anticipos:', merge_format)
        sheet.merge_range("AT" + str(row - 1) + ":" + "AU" +
                          str(row - 1), 'Anticipo Aguinaldo:', merge_format)
        sheet.merge_range("AV" + str(row - 1) + ":" + "AW" +
                          str(row - 1), 'Credito Social:', merge_format)
        sheet.merge_range("AX" + str(row - 1) + ":" + "AY" +
                          str(row - 1), 'Ahorro AFP:', merge_format)
        sheet.merge_range("AZ" + str(row - 1) + ":" + "BA" +
                          str(row - 1), 'Ahorro APV:', merge_format)
        sheet.merge_range("BB" + str(row - 1) + ":" + "BC" +
                          str(row - 1), 'Ahorro CCAF:', merge_format)
        sheet.merge_range("BD" + str(row - 1) + ":" + "BE" +
                          str(row - 1), 'Seg. de Vida CCAF:', merge_format)
        sheet.merge_range("BF" + str(row - 1) + ":" + "BG" +
                          str(row - 1), 'Ptmo. Empresa:', merge_format)
        sheet.merge_range("BH" + str(row - 1) + ":" + "BI" +
                          str(row - 1), 'Retencion Judicial:', merge_format)
        sheet.merge_range("BJ" + str(row - 1) + ":" + "BK" +
                          str(row - 1), 'Total Descuentos:', merge_format)
        sheet.merge_range("BL" + str(row - 1) + ":" + "BM" +
                          str(row - 1), 'Liquido A Pagar:', merge_format)
        return sheet

    def data_format(self,sheet,row,merge_format_data,payslip,is_bonus=False):
        if is_bonus:
            self.get_values(sheet, "O" + str(row) + ":" + "Q" + str(row),
                            'AGUINALDO', merge_format_data, payslip)
            self.get_values(sheet, "R" + str(row) + ":" + "S" + str(row),
                            'HORAS DESCUENTO', merge_format_data, payslip)
            self.get_values(sheet, "T" + str(row) + ":" + "U" + str(row),
                            'TOTAL IMPONIBLE', merge_format_data, payslip)
            self.get_values(sheet, "V" + str(row) + ":" + "W" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "X" + str(row) + ":" + "Y" + str(row),
                            'MOVILACION', merge_format_data, payslip)
            self.get_values(sheet, "Z" + str(row) + ":" + "AA" + str(row),
                            'COLACION', merge_format_data, payslip)
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
            return sheet
        else:
            self.get_values(sheet, "O" + str(row) + ":" + "Q" + str(row),
                            'AGUINALDO', merge_format_data, payslip)
            self.get_values(sheet, "O" + str(row) + ":" + "P" + str(row),
                            'HORAS DESCUENTO', merge_format_data, payslip)
            self.get_values(sheet, "Q" + str(row) + ":" + "R" + str(row),
                            'TOTAL IMPONIBLE', merge_format_data, payslip)
            self.get_values(sheet, "S" + str(row) + ":" + "T" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "U" + str(row) + ":" + "V" + str(row),
                            'MOVILACION', merge_format_data, payslip)
            self.get_values(sheet, "W" + str(row) + ":" + "X" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "Y" + str(row) + ":" + "Z" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AA" + str(row) + ":" + "AB" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AC" + str(row) + ":" + "AD" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AE" + str(row) + ":" + "AF" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AG" + str(row) + ":" + "AH" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AI" + str(row) + ":" + "AJ" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AK" + str(row) + ":" + "AL" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AM" + str(row) + ":" + "AN" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AO" + str(row) + ":" + "AP" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AQ" + str(row) + ":" + "AR" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AS" + str(row) + ":" + "AT" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AU" + str(row) + ":" + "AV" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AW" + str(row) + ":" + "AX" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AY" + str(row) + ":" + "AZ" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BA" + str(row) + ":" + "BB" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BC" + str(row) + ":" + "BD" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BE" + str(row) + ":" + "BF" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BG" + str(row) + ":" + "BH" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "BI" + str(row) + ":" + "BJ" + str(row),
                            'COLACION', merge_format_data, payslip)
            return sheet
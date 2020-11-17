import base64
import csv
import datetime
import io
import logging
import time
from datetime import datetime

import xlsxwriter
from dateutil import relativedelta
from odoo import api, fields, models


class WizardHrPaySlip(models.TransientModel):
    _name = "wizard.hr.payslip"
    _description = 'XLSX Report'

    delimiter = {
        'comma': ',',
        'dot_coma': ';',
        'tab': '\t',
    }
    quotechar = {
        'colon': '"',
        'semicolon': "'",
        'none': '',
    }

    company_id = fields.Many2one('res.partner', domain=[('id', 'in', ('423', '1', '1000', '79'))])

    report = fields.Binary(string='Descarge aqui =>',
                           default=lambda self: self.env['wizard.hr.payslip'].search([])[-1].report)

    month = fields.Selection(
        [('Enero', 'Enero'), ('Febrero', 'Febrero'), ('Marzo', 'Marzo'), ('Abril', 'Abril'), ('Mayo', 'Mayo'),
         ('Junio', 'Junio'), ('Julio', 'Julio'),
         ('Agosto', 'Agosto'), ('Septiembre', 'Septiembre'), ('Octubre', 'Octubre'), ('Noviembre', 'Noviembre'),
         ('Diciembre', 'Diciembre'), ], string="Mes")

    years = fields.Integer(string="Años", default=int(datetime.now().year))

    all = fields.Boolean('Todos las compañias')

    date_from = fields.Date('Fecha Inicial', required=True, default=lambda self: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Fecha Final', required=True, default=lambda self: str(
        datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    file_data = fields.Binary('Archivo Generado',
                              default=lambda self: self.env['wizard.hr.payslip'].search([])[-1].file_data)
    file_name = fields.Char('Nombre de archivo',
                            default=lambda self: self.env['wizard.hr.payslip'].search([])[-1].file_name)
    delimiter_option = fields.Selection([
        ('colon', 'Comillas Dobles(")'),
        ('semicolon', "Comillas Simples(')"),
        ('none', "Ninguno"),
    ], string='Separador de Texto', default='colon', required=True)
    delimiter_field_option = fields.Selection([
        ('comma', 'Coma(,)'),
        ('dot_coma', "Punto y coma(;)"),
        ('tab', "Tabulador"),
    ], string='Separador de Campos', default='dot_coma', required=True)

    report_name = fields.Char('')

    @api.multi
    def print_report_xlsx(self):
        file_name = 'temp'
        workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
        if self.all:
            worksheet_service = workbook.add_worksheet(self.env['res.partner'].search([('id', '=', 423)]).name)
            worksheet_export = workbook.add_worksheet(self.env['res.partner'].search([('id', '=', 1)]).name)
            worksheet_private = workbook.add_worksheet(self.env['res.partner'].search([('id', '=', 1000)]).name)
        else:
            worksheet = workbook.add_worksheet(self.company_id.name)
        indicadores_id = self.env['hr.indicadores'].search(
            [('name', '=', '{} {}'.format(self.month, self.years)), ('state', '=', 'done')])
        if not indicadores_id:
            raise models.ValidationError('No existen datos de este mes')
        merge_format_title = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        merge_format_string = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        merge_format_number = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '$#'
        })
        if self.all:
            worksheet_service.merge_range(
                "B2:E2", "Informe: Libro de Remuneraciones", merge_format_title)
            worksheet_service.merge_range("B3:E3", "Mes a procesar : {}".format(
                '{} {}'.format(self.month, self.years)), merge_format_title)
            worksheet_service.merge_range('B4:E4', "Compañia : {}".format(
                self.company_id.name
            ), merge_format_title)
            worksheet_export.merge_range(
                "B2:E2", "Informe: Libro de Remuneraciones", merge_format_title)
            worksheet_export.merge_range("B3:E3", "Mes a procesar : {}".format(
                '{} {}'.format(self.month, self.years)), merge_format_title)
            worksheet_export.merge_range('B4:E4', "Compañia : {}".format(
                self.company_id.name
            ), merge_format_title)
            worksheet_private.merge_range(
                "B2:E2", "Informe: Libro de Remuneraciones", merge_format_title)
            worksheet_private.merge_range("B3:E3", "Mes a procesar : {}".format(
                '{} {}'.format(self.month, self.years)), merge_format_title)
            worksheet_private.merge_range('B4:E4', "Compañia : {}".format(
                self.company_id.name
            ), merge_format_title)
        else:
            worksheet.merge_range(
                "B2:E2", "Informe: Libro de Remuneraciones", merge_format_title)
            worksheet.merge_range("B3:E3", "Mes a procesar : {}".format(
                '{} {}'.format(self.month, self.years)), merge_format_title)
            worksheet.merge_range('B4:E4', "Compañia : {}".format(
                self.company_id.name
            ), merge_format_title)
        employees = self.env['hr.employee']
        if self.all:
            employees_search = employees.search([('address_id', 'in', (423, 1, 1000, 79))])
        else:
            employees_search = employees.search([('address_id', '=', self.company_id.id)])
        if len(employees_search) == 0:
            raise models.ValidationError(
                'No existen empleados creados con este empresa,por favor verificar la direccion de trabajado del empleado')
        letter = 0
        row = 8

        payslips = self.env['hr.payslip'].search([('indicadores_id', '=', indicadores_id.id)])
        if self.all:
            self.set_title(employee=employees_search[0], employees=employees_search, sheet=worksheet_service,
                           merge_format=merge_format_title,
                           merge_format_string=merge_format_string, merge_format_number=merge_format_number,
                           payslips=payslips, row=row, indicadores_id=indicadores_id)
            self.set_title(employee=employees_search[0], employees=employees_search, sheet=worksheet_export,
                           merge_format=merge_format_title,
                           merge_format_string=merge_format_string, merge_format_number=merge_format_number,
                           payslips=payslips, row=row, indicadores_id=indicadores_id)
            self.set_title(employee=employees_search[0], employees=employees_search, sheet=worksheet_private,
                           merge_format=merge_format_title,
                           merge_format_string=merge_format_string, merge_format_number=merge_format_number,
                           payslips=payslips, row=row, indicadores_id=indicadores_id)
        else:
            self.set_title(employee=employees_search[0], employees=employees_search, sheet=worksheet, merge_format=merge_format_title,
                           merge_format_string=merge_format_string, merge_format_number=merge_format_number,
                           payslips=payslips, row=row, indicadores_id=indicadores_id)
        for emp in employees_search:
            if not payslips.filtered(lambda a: a.employee_id.id == emp.id and a.state == 'done'):
                continue
            if self.all:
                if emp.address_id.id == 423:
                    self.set_data(employee=emp, employees=employees, sheet=worksheet_service,
                                  merge_format=merge_format_title,
                                  merge_format_string=merge_format_string, merge_format_number=merge_format_number,
                                  payslips=payslips, row=row, indicadores_id=indicadores_id)
                elif emp.address_id.id == 1:
                    self.set_data(employee=emp, employees=employees, sheet=worksheet_export,
                                  merge_format=merge_format_title,
                                  merge_format_string=merge_format_string, merge_format_number=merge_format_number,
                                  payslips=payslips, row=row, indicadores_id=indicadores_id)
                elif emp.address_id.id == 1000:
                    raise models.UserError(worksheet_private)
                    self.set_data(employee=emp, employees=employees, sheet=worksheet_private,
                                  merge_format=merge_format_title,
                                  merge_format_string=merge_format_string, merge_format_number=merge_format_number,
                                  payslips=payslips, row=row, indicadores_id=indicadores_id)
                else:
                    continue
            else:
                self.set_data(employee=emp, employees=employees, sheet=worksheet, merge_format=merge_format_title,
                              merge_format_string=merge_format_string, merge_format_number=merge_format_number,
                              payslips=payslips, row=row, indicadores_id=indicadores_id)
            row += 1

        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        self.write({'report': file_base64, 'report_name': 'Libro de Remuneraciones {}'.format(indicadores_id.name)})
        return {
            "type": "ir.actions.do_nothing",
        }

    def set_title(self, employee, employees, sheet, merge_format, merge_format_string, merge_format_number, payslips,
                  row, indicadores_id):
        sheet.merge_range("A" + str(row - 1) + ":" + "D" +
                          str(row - 1), 'Nombre:', merge_format)
        sheet.merge_range("E" + str(row - 1) + ":" + "F" +
                          str(row - 1), 'RUT:', merge_format)
        sheet.merge_range("G" + str(row - 1) + ":" + "H" +
                          str(row - 1), 'Sueldo Base:', merge_format)
        sheet.merge_range("I" + str(row - 1) + ":" + "J" +
                          str(row - 1), 'Grat Legal:', merge_format)
        sheet.merge_range("K" + str(row - 1) + ":" + "L" +
                          str(row - 1), 'Ctda Dias Trabajados:', merge_format)
        sheet.merge_range("M" + str(row - 1) + ":" + "N" +
                          str(row - 1), 'Ctda Horas Extra:', merge_format)
        sheet.merge_range("O" + str(row - 1) + ":" + "P" +
                          str(row - 1), 'Horas Extra:', merge_format)
        sheet.merge_range("Q" + str(row - 1) + ":" + "R" +
                          str(row - 1), 'Bono de Produccion:', merge_format)
        sheet.merge_range("S" + str(row - 1) + ":" + "T" +
                          str(row - 1), 'Bono de Responsabilidad:', merge_format)
        sheet.merge_range("U" + str(row - 1) + ":" + "V" +
                          str(row - 1), 'Bono de Permanencia:', merge_format)
        sheet.merge_range("W" + str(row - 1) + ":" + "X" +
                          str(row - 1), 'Bonos Imponibles:', merge_format)
        if 'Septiembre' in indicadores_id[-1].name:
            sheet = self.title_format(sheet, row, merge_format, 'Aguinaldo Fiestas Patrias:')
        elif 'Diciembre' in indicadores_id[-1].name:
            sheet = self.title_format(sheet, row, merge_format, 'Aguinaldo Navidad:')
        else:
            sheet = self.title_format(sheet, row, merge_format)

    def set_data(self, employee, employees, sheet, merge_format, merge_format_string, merge_format_number, payslips,
                 row, indicadores_id):
        raise models.ValidationError(sheet.)
        if employee.id == employees[0].id:
            self.set_title(employee=employee, employees=employees, sheet=sheet, merge_format=merge_format,
                           merge_format_string=merge_format_string, merge_format_number=merge_format_number,
                           payslips=payslips, row=row, indicadores_id=indicadores_id)
        sheet.merge_range("A" + str(row) + ":" + "D" + str(row),
                          employee.display_name, merge_format_string)
        sheet.merge_range("E" + str(row) + ":" + "F" + str(row),
                          employee.identification_id, merge_format_string)

        payslip = payslips.filtered(
            lambda a: a.employee_id.id == employee.id and a.state == 'done')
        self.get_values(sheet, "G" + str(row) + ":" + "H" + str(row),
                        'SUELDO BASE', merge_format_number, payslip)
        self.get_values(sheet, "I" + str(row) + ":" + "J" + str(row),
                        'GRATIFICACION LEGAL', merge_format_number, payslip)
        sheet.merge_range("K" + str(row) + ":" + "L" + str(row),
                          payslip.worked_days_line_ids.filtered(lambda a: a.code == 'WORK100').number_of_days,
                          merge_format_string)
        sheet.merge_range("M" + str(row) + ":" + "N" + str(row),
                          payslip.input_line_ids.filtered(lambda a: a.code == 'HEX50').amount,
                          merge_format_string)
        self.get_values(sheet, "O" + str(row) + ":" + "P" + str(row),
                        'HORAS EXTRA ART 32', merge_format_number, payslip)
        if payslip.mapped('line_ids').filtered(lambda a: a.name == "BONO DE PRODUCCION").total == 0:
            sheet.merge_range("Q" + str(row) + ":" + "R" + str(row),
                              '',
                              merge_format_number)
        else:
            sheet.merge_range("Q" + str(row) + ":" + "R" + str(row),
                              payslip.mapped('line_ids').filtered(lambda a: a.name == "BONO DE PRODUCCION").total,
                              merge_format_number)
        if payslip.mapped('line_ids').filtered(lambda a: a.name == "BONO DE RESPONSABILIDAD").total == 0:
            sheet.merge_range("S" + str(row) + ":" + "T" + str(row),
                              '',
                              merge_format_number)
        else:
            sheet.merge_range("S" + str(row) + ":" + "T" + str(row),
                              payslip.mapped('line_ids').filtered(lambda a: a.name == "BONO DE RESPONSABILIDAD").total,
                              merge_format_number)
        if payslip.mapped('line_ids').filtered(lambda a: a.name == "BONO DE PERMANENCIA").total == 0:
            sheet.merge_range("U" + str(row) + ":" + "V" + str(row),
                              '',
                              merge_format_number)
        else:
            sheet.merge_range("U" + str(row) + ":" + "V" + str(row),
                              payslip.mapped('line_ids').filtered(lambda a: a.name == "BONO DE PERMANENCIA").total,
                              merge_format_number)
        if sum(payslip.mapped('line_ids').filtered(
                lambda a: 'BONO' in a.name and a.category_id.name == 'Imponible').mapped('total')) == 0:
            sheet.merge_range("W" + str(row) + ":" + "X" + str(row),
                              '',
                              merge_format_number)
        else:
            sheet.merge_range("W" + str(row) + ":" + "X" + str(row),
                              sum(payslip.mapped('line_ids').filtered(
                                  lambda a: 'BONO' in a.name and a.category_id.name == 'Imponible').mapped('total')),
                              merge_format_number)
        if 'Septiembre' in indicadores_id[-1].name or 'Diciembre' in indicadores_id[-1].name:
            sheet_service = self.data_format(sheet, row, merge_format_number, payslip, is_bonus=True)
        else:
            sheet_service = self.data_format(sheet, row, merge_format_number, payslip)

    def get_values(self, sheet, set_in, to_search, format_data, payslip):
        if not payslip.mapped('line_ids').filtered(lambda a: a.name == to_search).total:
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
        sheet.merge_range()

    def title_format(self, sheet, row, merge_format, title=''):
        if title != '':
            sheet.set_column(1, row, 30)
            sheet.merge_range("Y" + str(row - 1) + ":" + "Z" + str(row - 1),
                              title, merge_format)
            sheet.merge_range(
                "AA" + str(row - 1) + ":" + "AB" + str(row - 1), 'Horas de Descuento:', merge_format)
            sheet.merge_range("AC" + str(row - 1) + ":" + "AD" +
                              str(row - 1), 'Total Imponible:', merge_format)
            sheet.merge_range("AE" + str(row - 1) + ":" + "AF" +
                              str(row - 1), 'Colacion', merge_format)
            sheet.merge_range("AG" + str(row - 1) + ":" + "AH" +
                              str(row - 1), 'Movilizacion:', merge_format)
            sheet.merge_range("AI" + str(row - 1) + ":" + "AJ" +
                              str(row - 1), 'Asig Familiar:', merge_format)
            sheet.merge_range("AK" + str(row - 1) + ":" + "AL" +
                              str(row - 1), 'Asig Varias:', merge_format)
            sheet.merge_range("AM" + str(row - 1) + ":" + "AN" +
                              str(row - 1), 'Total No Imponible:', merge_format)
            sheet.merge_range("AO" + str(row - 1) + ":" + "AP" +
                              str(row - 1), 'Total Haberes:', merge_format)
            sheet.merge_range("AQ" + str(row - 1) + ":" + "AR" +
                              str(row - 1), 'AFP:', merge_format)
            sheet.merge_range("AS" + str(row - 1) + ":" + "AT" +
                              str(row - 1), 'Salud:', merge_format)
            sheet.merge_range("AU" + str(row - 1) + ":" + "AV" +
                              str(row - 1), 'Seg. Cesantia:', merge_format)
            sheet.merge_range("AW" + str(row - 1) + ":" + "AX" +
                              str(row - 1), 'Impto. Unico:', merge_format)
            sheet.merge_range("AY" + str(row - 1) + ":" + "AZ" +
                              str(row - 1), 'Otros AFP:', merge_format)
            sheet.merge_range("BA" + str(row - 1) + ":" + "BB" +
                              str(row - 1), 'Anticipos:', merge_format)
            sheet.merge_range("BC" + str(row - 1) + ":" + "BD" +
                              str(row - 1), 'Anticipo Aguinaldo:', merge_format)
            sheet.merge_range("BE" + str(row - 1) + ":" + "BF" +
                              str(row - 1), 'Credito Social:', merge_format)
            sheet.merge_range("BG" + str(row - 1) + ":" + "BH" +
                              str(row - 1), 'Ahorro AFP:', merge_format)
            sheet.merge_range("BI" + str(row - 1) + ":" + "BJ" +
                              str(row - 1), 'Ahorro APV:', merge_format)
            sheet.merge_range("BK" + str(row - 1) + ":" + "BL" +
                              str(row - 1), 'Ahorro CCAF:', merge_format)
            sheet.merge_range("BM" + str(row - 1) + ":" + "BN" +
                              str(row - 1), 'Seg. de Vida CCAF:', merge_format)
            sheet.merge_range("BO" + str(row - 1) + ":" + "BP" +
                              str(row - 1), 'Ptmo. Empresa:', merge_format)
            sheet.merge_range("BQ" + str(row - 1) + ":" + "BR" +
                              str(row - 1), 'Retencion Judicial:', merge_format)
            sheet.merge_range("BS" + str(row - 1) + ":" + "BT" +
                              str(row - 1), 'Total Descuentos:', merge_format)
            sheet.merge_range("BV" + str(row - 1) + ":" + "BX" +
                              str(row - 1), 'Liquido A Pagar:', merge_format)
        else:
            sheet.merge_range(
                "Y" + str(row - 1) + ":" + "Z" + str(row - 1), 'Horas de Descuento:', merge_format)
            sheet.merge_range("AA" + str(row - 1) + ":" + "AB" +
                              str(row - 1), 'Total Imponible:', merge_format)
            sheet.merge_range("AC" + str(row - 1) + ":" + "AD" +
                              str(row - 1), 'Colacion', merge_format)
            sheet.merge_range("AE" + str(row - 1) + ":" + "AF" +
                              str(row - 1), 'Movilizacion:', merge_format)
            sheet.merge_range("AG" + str(row - 1) + ":" + "AH" +
                              str(row - 1), 'Asig Familiar:', merge_format)
            sheet.merge_range("AI" + str(row - 1) + ":" + "AJ" +
                              str(row - 1), 'Asig Varias:', merge_format)
            sheet.merge_range("AK" + str(row - 1) + ":" + "AL" +
                              str(row - 1), 'Total No Imponible:', merge_format)
            sheet.merge_range("AM" + str(row - 1) + ":" + "AN" +
                              str(row - 1), 'Total Haberes:', merge_format)
            sheet.merge_range("AO" + str(row - 1) + ":" + "AP" +
                              str(row - 1), 'AFP:', merge_format)
            sheet.merge_range("AQ" + str(row - 1) + ":" + "AR" +
                              str(row - 1), 'Salud:', merge_format)
            sheet.merge_range("AS" + str(row - 1) + ":" + "AT" +
                              str(row - 1), 'Seg. Cesantia:', merge_format)
            sheet.merge_range("AU" + str(row - 1) + ":" + "AV" +
                              str(row - 1), 'Impto. Unico:', merge_format)
            sheet.merge_range("AW" + str(row - 1) + ":" + "AX" +
                              str(row - 1), 'Otros AFP:', merge_format)
            sheet.merge_range("AY" + str(row - 1) + ":" + "AZ" +
                              str(row - 1), 'Anticipos:', merge_format)
            sheet.merge_range("BA" + str(row - 1) + ":" + "BB" +
                              str(row - 1), 'Anticipo Aguinaldo:', merge_format)
            sheet.merge_range("BC" + str(row - 1) + ":" + "BD" +
                              str(row - 1), 'Credito Social:', merge_format)
            sheet.merge_range("BE" + str(row - 1) + ":" + "BF" +
                              str(row - 1), 'Ahorro AFP:', merge_format)
            sheet.merge_range("BG" + str(row - 1) + ":" + "BH" +
                              str(row - 1), 'Ahorro APV:', merge_format)
            sheet.merge_range("BI" + str(row - 1) + ":" + "BJ" +
                              str(row - 1), 'Ahorro CCAF:', merge_format)
            sheet.merge_range("BK" + str(row - 1) + ":" + "BL" +
                              str(row - 1), 'Seg. de Vida CCAF:', merge_format)
            sheet.merge_range("BM" + str(row - 1) + ":" + "BN" +
                              str(row - 1), 'Ptmo. Empresa:', merge_format)
            sheet.merge_range("BO" + str(row - 1) + ":" + "BP" +
                              str(row - 1), 'Retencion Judicial:', merge_format)
            sheet.merge_range("BQ" + str(row - 1) + ":" + "BR" +
                              str(row - 1), 'Total Descuentos:', merge_format)
            sheet.merge_range("BS" + str(row - 1) + ":" + "BT" +
                              str(row - 1), 'Liquido A Pagar:', merge_format)
        return sheet

    def data_format(self, sheet, row, merge_format_data, payslip, is_bonus=False):
        if is_bonus:
            self.get_values(sheet, "Y" + str(row) + ":" + "Z" + str(row),
                            'AGUINALDO', merge_format_data, payslip)
            self.get_values(sheet, "AA" + str(row) + ":" + "AB" + str(row),
                            'HORAS DESCUENTO', merge_format_data, payslip)
            self.get_values(sheet, "AC" + str(row) + ":" + "AD" + str(row),
                            'TOTAL IMPONIBLE', merge_format_data, payslip)
            self.get_values(sheet, "AE" + str(row) + ":" + "AF" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AG" + str(row) + ":" + "AH" + str(row),
                            'MOVILACION', merge_format_data, payslip)
            self.get_values(sheet, "AI" + str(row) + ":" + "AJ" + str(row),
                            'ASIGNACION FAMILIAR', merge_format_data, payslip)
            self.get_values(sheet, "AK" + str(row) + ":" + "AL" + str(row),
                            'ASIGNACION VARIAS', merge_format_data, payslip)
            self.get_values(sheet, "AM" + str(row) + ":" + "AN" + str(row),
                            'TOTAL NO IMPONIBLE', merge_format_data, payslip)
            self.get_values(sheet, "AO" + str(row) + ":" + "AN" + str(row),
                            'TOTAL HABERES', merge_format_data, payslip)
            self.get_values(sheet, "AQ" + str(row) + ":" + "AR" + str(row),
                            'PREVISION', merge_format_data, payslip)
            self.get_values(sheet, "AS" + str(row) + ":" + "AT" + str(row),
                            'SALUD', merge_format_data, payslip)
            self.get_values(sheet, "AU" + str(row) + ":" + "AV" + str(row),
                            'SEGURO CESANTIA', merge_format_data, payslip)
            self.get_values(sheet, "AW" + str(row) + ":" + "AX" + str(row),
                            'IMPUESTO UNICO', merge_format_data, payslip)
            self.get_values(sheet, "AY" + str(row) + ":" + "AZ" + str(row),
                            'OTROS AFP', merge_format_data, payslip)
            self.get_values(sheet, "BA" + str(row) + ":" + "BB" + str(row),
                            'ANTICIPO DE SUELDO', merge_format_data, payslip)
            self.get_values(sheet, "BC" + str(row) + ":" + "BD" + str(row),
                            'ANTICIPO DE AGUINALDO', merge_format_data, payslip)
            self.get_values(sheet, "BE" + str(row) + ":" + "BF" + str(row),
                            'CREDITO SOCIAL', merge_format_data, payslip)
            self.get_values(sheet, "BG" + str(row) + ":" + "BH" + str(row),
                            'AHORRO AFP', merge_format_data, payslip)
            self.get_values(sheet, "BI" + str(row) + ":" + "BJ" + str(row),
                            'APORTE AL AHORRO VOLUNTARIO', merge_format_data, payslip)
            self.get_values(sheet, "BK" + str(row) + ":" + "BL" + str(row),
                            'AHORRO CAJA DE COMPENSACION', merge_format_data, payslip)
            self.get_values(sheet, "BM" + str(row) + ":" + "BN" + str(row),
                            'SEGURO VIDA CAJA DE COMPENSACION', merge_format_data, payslip)
            self.get_values(sheet, "BO" + str(row) + ":" + "BP" + str(row),
                            'PRESTAMOS EMPRESA', merge_format_data, payslip)
            self.get_values(sheet, "BQ" + str(row) + ":" + "BR" + str(row),
                            'RETENCION JUDICIAL', merge_format_data, payslip)
            self.get_values(sheet, "BS" + str(row) + ":" + "BT" + str(row),
                            'TOTAL DESCUENTOS', merge_format_data, payslip)
            self.get_values(sheet, "BU" + str(row) + ":" + "BV" + str(row),
                            'ALCANCE LIQUIDO', merge_format_data, payslip)
            return sheet
        else:
            self.get_values(sheet, "Y" + str(row) + ":" + "Z" + str(row),
                            'HORAS DESCUENTO', merge_format_data, payslip)
            self.get_values(sheet, "AA" + str(row) + ":" + "AB" + str(row),
                            'TOTAL IMPONIBLE', merge_format_data, payslip)
            self.get_values(sheet, "AC" + str(row) + ":" + "AD" + str(row),
                            'COLACION', merge_format_data, payslip)
            self.get_values(sheet, "AE" + str(row) + ":" + "AF" + str(row),
                            'MOVILACION', merge_format_data, payslip)
            self.get_values(sheet, "AG" + str(row) + ":" + "AH" + str(row),
                            'ASIGNACION FAMILIAR', merge_format_data, payslip)
            self.get_values(sheet, "AI" + str(row) + ":" + "AJ" + str(row),
                            'ASIGNACIONES VARIAS', merge_format_data, payslip)
            self.get_values(sheet, "AK" + str(row) + ":" + "AL" + str(row),
                            'TOTAL NO IMPONIBLE', merge_format_data, payslip)
            self.get_values(sheet, "AM" + str(row) + ":" + "AN" + str(row),
                            'TOTAL HABERES', merge_format_data, payslip)
            self.get_values(sheet, "AO" + str(row) + ":" + "AP" + str(row),
                            'PREVISION', merge_format_data, payslip)
            self.get_values(sheet, "AQ" + str(row) + ":" + "AR" + str(row),
                            'SALUD', merge_format_data, payslip)
            self.get_values(sheet, "AS" + str(row) + ":" + "AT" + str(row),
                            'SEGURO CESANTIA', merge_format_data, payslip)
            self.get_values(sheet, "AU" + str(row) + ":" + "AV" + str(row),
                            'IMPUESTO UNICO', merge_format_data, payslip)
            self.get_values(sheet, "AW" + str(row) + ":" + "AX" + str(row),
                            'OTROS AFP', merge_format_data, payslip)
            self.get_values(sheet, "AY" + str(row) + ":" + "AZ" + str(row),
                            'ANTICIPO DE SUELDO', merge_format_data, payslip)
            self.get_values(sheet, "BA" + str(row) + ":" + "BB" + str(row),
                            'ANTICIPO DE AGUINALDO', merge_format_data, payslip)
            self.get_values(sheet, "BC" + str(row) + ":" + "BD" + str(row),
                            'CREDITO SOCIAL', merge_format_data, payslip)
            self.get_values(sheet, "BE" + str(row) + ":" + "BF" + str(row),
                            'AHORRO AFP', merge_format_data, payslip)
            self.get_values(sheet, "BG" + str(row) + ":" + "BH" + str(row),
                            'APORTE AL AHORRO VOLUNTARIO', merge_format_data, payslip)
            self.get_values(sheet, "BI" + str(row) + ":" + "BJ" + str(row),
                            'AHORRO CCAF', merge_format_data, payslip)
            self.get_values(sheet, "BK" + str(row) + ":" + "BL" + str(row),
                            'SEGURO DE VIDA CCAF', merge_format_data, payslip)
            self.get_values(sheet, "BM" + str(row) + ":" + "BN" + str(row),
                            'PRESTAMOS EMPRESA', merge_format_data, payslip)
            self.get_values(sheet, "BO" + str(row) + ":" + "BP" + str(row),
                            'RETENCION JUDICIAL', merge_format_data, payslip)
            self.get_values(sheet, "BQ" + str(row) + ":" + "BR" + str(row),
                            'TOTAL DESCUENTOS', merge_format_data, payslip)
            self.get_values(sheet, "BS" + str(row) + ":" + "BT" + str(row),
                            'ALCANCE LIQUIDO', merge_format_data, payslip)
            return sheet

    def set_total(self, sheet, set_in, to_search, format_data, payslips):
        return sheet.merge_range(set_in, sum(
            payslips.mapped('line_ids').filtered(lambda a: a.name == to_search).mapped('total')))

    @api.model
    def get_nacionalidad(self, employee):
        # 0 chileno, 1 extranjero, comparar con el pais de la compañia
        if employee == 46:
            return 0
        else:
            return 1

    @api.model
    def get_tipo_pago(self, employee):
        # 01 Remuneraciones del mes
        # 02 Gratificaciones
        # 03 Bono Ley de Modernizacion Empresas Publicas
        # TODO: en base a que se elije el tipo de pago???
        return 1

    @api.model
    def get_regimen_provisional(self, contract):
        if contract.pension is True:
            return 'SIP'
        else:
            return 'AFP'

    @api.model
    def get_tipo_trabajador(self, employee):
        if employee.type_id is False:
            return 0
        else:
            tipo_trabajador = employee.type_id.id_type

        # Codigo    Glosa
        # id_type
        # 0        Activo (No Pensionado)
        # 1        Pensionado y cotiza
        # 2        Pensionado y no cotiza
        # 3        Activo > 65 años (nunca pensionado)
        return tipo_trabajador

    @api.model
    def get_dias_trabajados(self, payslip):
        worked_days = 0
        if payslip:
            for line in payslip.worked_days_line_ids:
                if line.code == 'WORK100':
                    worked_days = line.number_of_days
        return worked_days

    @api.model
    def get_cost_center(self, contract):
        cost_center = "1"
        if contract.analytic_account_id:
            cost_center = contract.analytic_account_id.code
        return cost_center

    @api.model
    def get_tipo_linea(self, payslip):
        # 00 Linea Principal o Base
        # 01 Linea Adicional
        # 02 Segundo Contrato
        # 03 Movimiento de Personal Afiliado Voluntario
        return '00'

    @api.model
    def get_tramo_asignacion_familiar(self, payslip, valor):
        try:
            if payslip.contract_id.data_id.name:
                return payslip.contract_id.data_id.name.split(' ')[1]
            else:
                if payslip.contract_id.carga_familiar != 0 and payslip.indicadores_id.asignacion_familiar_tercer >= payslip.contract_id.wage and payslip.contract_id.pension is False:
                    if payslip.indicadores_id.asignacion_familiar_primer >= valor:
                        return 'A'
                elif payslip.indicadores_id.asignacion_familiar_segundo >= valor:
                    return 'B'
                elif payslip.indicadores_id.asignacion_familiar_tercer >= valor:
                    return 'C'
                else:
                    return 'D'
        except:
            return 'D'

    def get_payslip_lines_value(self, obj, regla):
        try:
            linea = obj.search([('code', '=', regla)])
            valor = linea.amount
            return valor
        except:
            return '0'

    def get_payslip_lines_value_2(self, obj, regla):
        valor = 0
        lineas = self.env['hr.payslip.line']
        detalle = lineas.search([('slip_id', '=', obj.id), ('code', '=', regla)])
        data = str(detalle.amount).split('.')[0]
        valor = data
        return valor

    @api.model
    def get_imponible_afp(self, payslip, TOTIM):
        TOTIM_2 = float(TOTIM)
        if payslip.contract_id.pension is True:
            return '0'
        elif TOTIM_2 >= round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf):
            return round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf)
        else:
            return round(TOTIM_2)

    @api.model
    def get_imponible_afp_2(self, payslip, TOTIM, LIC):
        LIC_2 = float(LIC)
        TOTIM_2 = float(TOTIM)
        if LIC_2 > 0:
            TOTIM = LIC
        if payslip.contract_id.pension is True:
            return '0.0'
        elif TOTIM_2 >= round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf):
            data = str(float(round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf))).split('.')
            return data[0]
        else:
            data = str(float(round(TOTIM_2))).split('.')
            return data[0]

    @api.model
    def get_imponible_mutual(self, payslip, TOTIM):
        TOTIM_2 = float(TOTIM)
        if payslip.contract_id.mutual_seguridad is False:
            return 0
        elif payslip.contract_id.type_id.name == 'Sueldo Empresarial':
            return 0
        elif TOTIM_2 >= round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf):
            return round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf)
        else:
            return round(TOTIM_2)

    @api.model
    def get_imponible_seguro_cesantia(self, payslip, TOTIM, LIC):
        LIC_2 = float(LIC)
        TOTIM_2 = float(TOTIM)
        if LIC_2 > 0:
            TOTIM = LIC
        if payslip.contract_id.pension is True:
            return 0
        elif payslip.contract_id.type_id.name == 'Sueldo Empresarial':
            return 0
        elif TOTIM_2 >= round(payslip.indicadores_id.tope_imponible_seguro_cesantia * payslip.indicadores_id.uf):
            data = str(
                float(round(payslip.indicadores_id.tope_imponible_seguro_cesantia * payslip.indicadores_id.uf))).split(
                '.')
            return data[0]
        else:
            data = str(float(round(TOTIM_2))).split('.')
            return data[0]

    @api.model
    def get_imponible_salud(self, payslip, TOTIM):
        result = 0
        TOTAL = float(TOTIM)
        if TOTAL >= round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf):
            data = str(float(round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf))).split('.')
            return data[0]
        else:
            data = str(float(round(TOTAL))).split('.')
            return data[0]

    @api.model
    def _acortar_str(self, texto, size=1):
        c = 0
        cadena = ""
        while c < size and c < len(texto):
            cadena += texto[c]
            c += 1
        return cadena

    @api.model
    def _arregla_str(self, texto, size=1):
        c = 0
        cadena = ""
        special_chars = [
            ['á', 'a'],
            ['é', 'e'],
            ['í', 'i'],
            ['ó', 'o'],
            ['ú', 'u'],
            ['ñ', 'n'],
            ['Á', 'A'],
            ['É', 'E'],
            ['Í', 'I'],
            ['Ó', 'O'],
            ['Ú', 'U'],
            ['Ñ', 'N']]

        while c < size and c < len(texto):
            cadena += texto[c]
            c += 1
        for char in special_chars:
            try:
                cadena = cadena.replace(char[0], char[1])
            except:
                pass
        return cadena

    @api.multi
    def action_generate_csv(self):
        employee_model = self.env['hr.employee']
        payslip_model = self.env['hr.payslip']
        payslip_line_model = self.env['hr.payslip.line']
        sexo_data = {'male': "M",
                     'female': "F",
                     }
        _logger = logging.getLogger(__name__)
        country_company = self.env.user.company_id.country_id
        output = io.StringIO()
        if self.delimiter_option == 'none':
            writer = csv.writer(output, delimiter=self.delimiter[self.delimiter_field_option], quoting=csv.QUOTE_NONE)
        else:
            writer = csv.writer(output, delimiter=self.delimiter[self.delimiter_field_option],
                                quotechar=self.quotechar[self.delimiter_option], quoting=csv.QUOTE_NONE)
        # Debemos colocar que tome todo el mes y no solo el día exacto TODO
        payslip_recs = payslip_model.search([('date_from', '=', self.date_from), ('state', '=', 'done'),
                                             ('employee_id.address_id', '=', self.company_id.id)
                                             ])

        date_start = self.date_from
        date_stop = self.date_to
        date_start_format = date_start.strftime("%m%Y")
        date_stop_format = date_stop.strftime("%m%Y")
        line_employee = []
        rut = ""
        rut_dv = ""
        rut_emp = ""
        rut_emp_dv = ""

        try:
            rut_emp, rut_emp_dv = self.env.user.company_id.vat.split("-")
            rut_emp = rut_emp.replace('.', '')
        except:
            pass

        for payslip in payslip_recs:
            payslip_line_recs = payslip_line_model.search([('slip_id', '=', payslip.id)])
            rut = ""
            rut_dv = ""
            rut, rut_dv = payslip.employee_id.identification_id.split("-")
            rut = rut.replace('.', '')
            line_employee = [self._acortar_str(rut, 11),
                             self._acortar_str(rut_dv, 1),
                             self._arregla_str(payslip.employee_id.last_name.upper(),
                                               30) if payslip.employee_id.last_name else "",
                             self._arregla_str(payslip.employee_id.mothers_name.upper(),
                                               30) if payslip.employee_id.mothers_name else "",
                             "%s %s" % (self._arregla_str(payslip.employee_id.firstname.upper(), 15),
                                        self._arregla_str(payslip.employee_id.middle_name.upper(),
                                                          15) if payslip.employee_id.middle_name else ''),
                             sexo_data.get(payslip.employee_id.gender, "") if payslip.employee_id.gender else "",
                             self.get_nacionalidad(payslip.employee_id.country_id.id),
                             self.get_tipo_pago(payslip.employee_id),
                             date_start_format,
                             date_stop_format,
                             # 11
                             self.get_regimen_provisional(payslip.contract_id),
                             # 12
                             "0",
                             # payslip.employee_id.type_id.id_type,
                             # 13
                             str(float(self.get_dias_trabajados(payslip and payslip[0] or False))).split('.')[0],
                             # 14
                             self.get_tipo_linea(payslip and payslip[0] or False),
                             # 15
                             payslip.movimientos_personal,
                             # 16 Fecha inicio movimiento personal (dia-mes-año)
                             # Si declara mov. personal 1, 3, 4, 5, 6, 7, 8 y 11 Fecha Desde
                             # es obligatoria y debe estar dentro del periodo de remun
                             payslip.date_from.strftime(
                                 "%d/%m/%Y") if payslip.movimientos_personal != '0' else '00/00/0000',
                             # payslip.date_from if payslip.date_from else '00/00/0000',
                             # 17 Fecha fin movimiento personal (dia-mes-año)
                             payslip.date_to.strftime(
                                 "%d/%m/%Y") if payslip.movimientos_personal != '0' else '00/00/0000',
                             # Si declara mov. personal 1, 3, 4, 5, 6, 7, 8 y 11 Fecha Desde
                             # es obligatoria y debe estar dentro del periodo de remun
                             # payslip.date_to if payslip.date_to else '00-00-0000',
                             self.get_tramo_asignacion_familiar(payslip,
                                                                self.get_payslip_lines_value_2(payslip, 'TOTIM')),
                             # 19 NCargas Simples
                             payslip.contract_id.carga_familiar,
                             payslip.contract_id.carga_familiar_maternal,
                             payslip.contract_id.carga_familiar_invalida,
                             # 22 Asignacion Familiar
                             self.get_payslip_lines_value_2(payslip, 'ASIGFAM') if self.get_payslip_lines_value_2(
                                 payslip, 'ASIGFAM') else "00",
                             # ASIGNACION FAMILIAR RETROACTIVA
                             "0",
                             # Refloategro Cargas Familiares
                             "0",
                             # 25 Solicitud Trabajador Joven TODO SUBSIDIO JOVEN
                             "N",
                             # 26
                             payslip.contract_id.afp_id.codigo if payslip.contract_id.afp_id.codigo else "00",
                             # 27
                             str(float(self.get_imponible_afp_2(payslip and payslip[0] or False,
                                                                self.get_payslip_lines_value_2(payslip, 'TOTIM'),
                                                                self.get_payslip_lines_value_2(payslip,
                                                                                               'IMPLIC')))).split('.')[
                                 0],
                             # AFP SIS APV 0 0 0 0 0 0
                             # 28
                             str(float(self.get_payslip_lines_value_2(payslip, 'PREV'))).split('.')[0],
                             str(float(self.get_payslip_lines_value_2(payslip, 'SIS'))).split('.')[0],
                             # 30 Cuenta de Ahorro Voluntario AFP
                             "0",
                             # 31 Renta Imp. Sust.AFP
                             "0",
                             # 32 Tasa Pactada (Sustit.)
                             "0",
                             # 33 Aporte Indemn. (Sustit.)
                             "0",
                             # 34 N Periodos (Sustit.)
                             "0",
                             # 35 Periodo desde (Sustit.)
                             "0",
                             # 36 Periodo Hasta (Sustit.)
                             "0",
                             # 37 Puesto de Trabajo Pesado
                             " ",
                             # 38 % Cotizacion Trabajo Pesado
                             "0",
                             # 39 Cotizacion Trabajo Pesado
                             "0",
                             # 3- Datos Ahorro Previsional Voluntario Individual
                             # 40 Código de la Institución APVI
                             payslip.contract_id.apv_id.codigo if self.get_payslip_lines_value_2(payslip,
                                                                                                 'APV') else "0",
                             # 41 Numero de Contrato APVI Strinng
                             "0",
                             # 42 Forma de Pago Ahorro
                             payslip.contract_id.forma_pago_apv if self.get_payslip_lines_value_2(payslip,
                                                                                                  'APV') else "0",
                             # 43 Cotización APVI 9(8) Monto en $ de la Cotización APVI
                             str(float(self.get_payslip_lines_value_2(payslip, 'APV'))).split('.')[
                                 0] if str(float(self.get_payslip_lines_value_2(payslip, 'APV'))).split('.')[
                                 0] else "0",
                             # 44 Cotizacion Depositos

                             # 45 Codigo Institucion Autorizada APVC
                             "0",
                             # 46 Numero de Contrato APVC TODO
                             " ",
                             # 47 Forma de Pago APVC
                             "0",
                             # 48 Cotizacion Trabajador APVC
                             "0",
                             # 49 Cotizacion Empleador APVC
                             "0",
                             # 50 RUT Afiliado Voluntario 9 (11)
                             "0",
                             # 51 DV Afiliado Voluntario
                             " ",
                             # 52 Apellido Paterno
                             " ",
                             # 53 Apellido Materno
                             " ",
                             # 54 Nombres
                             " ",
                             "0",

                             # Tabla N°7: Movimiento de Personal
                             # Código Glosa
                             # 0 Sin Movimiento en el Mes
                             # 1 Contratación a plazo indefinido
                             # 2 Retiro
                             # 3 Subsidios
                             # 4 Permiso Sin Goce de Sueldos
                             # 5 Incorporación en el Lugar de Trabajo
                             # 6 Accidentes del Trabajo
                             # 7 Contratación a plazo fijo
                             # 8 Cambio Contrato plazo fijo a plazo indefinido
                             # 11 Otros Movimientos (Ausentismos)
                             # 12 Reliquidación, Premio, Bono
                             # TODO LIQUIDACION

                             "00",
                             # 56 Fecha inicio movimiento personal (dia-mes-año)
                             "0",
                             # 57 Fecha fin movimiento personal (dia-mes-año)
                             "0",
                             # 58 Codigo de la AFP
                             "0",
                             # 59 Monto Capitalizacion Voluntaria
                             "0",
                             # 60 Monto Ahorro Voluntario
                             "0",
                             # 61 Numero de periodos de cotizacion
                             "0",
                             # 62 Codigo EX-Caja Regimen
                             "0",
                             # 63 Tasa Cotizacion Ex-Caja Prevision
                             "0",
                             # 64 Renta Imponible IPS    Obligatorio si es IPS Obligatorio si es IPS Obligatorio si es INP si no, 0000
                             self.get_payslip_lines_value_2(payslip,
                                                            'TOTIM') if payslip.contract_id.isapre_id.codigo == '07' else "0",
                             # 65 Cotizacion Obligatoria IPS
                             "0",
                             # 66 Renta Imponible Desahucio
                             "0",
                             # 67 Codigo Ex-Caja Regimen Desahucio
                             "0",
                             # 68 Tasa Cotizacion Desahucio Ex-Cajas
                             "0",
                             # 69 Cotizacion Desahucio
                             "0",
                             # 70 Cotizacion Fonasa
                             # "0",
                             self.get_payslip_lines_value_2(payslip,
                                                            'FONASA') if payslip.contract_id.isapre_id.codigo == '07' else "0",

                             # 71 Cotizacion Acc. Trabajo (ISL)
                             str(float(self.get_payslip_lines_value_2(payslip, 'ISL'))).split('.')[
                                 0] if self.get_payslip_lines_value_2(payslip, 'ISL') else "0",

                             # 0.93% de la Rta. Imp. (64) y es obligatorio para
                             # el empleador. Se paga a través de ISL sólo en
                             # casos en que no exista Mutual Asociada En otro
                             # caso se paga en la mutual respectiva. Datos no numérico

                             # 72 Bonificacion Ley 15.386
                             "0",
                             # 73 Descuento por cargas familiares de ISL
                             "0",
                             # 74 Bonos Gobierno
                             "0",
                             # 7- Datos Salud ISAPRE
                             # 75 Codigo Institucion de Salud
                             payslip.contract_id.isapre_id.codigo,
                             # 76 Numero del FUN
                             " " if payslip.contract_id.isapre_id.codigo == '07' else payslip.contract_id.isapre_fun if payslip.contract_id.isapre_fun else "",
                             # 77 Renta Imponible Isapre REVISAR  Tope Imponible Salud 5,201
                             # "0" if payslip.contract_id.isapre_id.codigo=='07' else self.get_payslip_lines_value_2(payslip,'TOTIM'),
                             "0" if payslip.contract_id.isapre_id.codigo == '07' else self.get_imponible_salud(
                                 payslip and payslip[0] or False, self.get_payslip_lines_value_2(payslip, 'TOTIM')),
                             # 78 Moneda Plan Isapre UF Pesos TODO Poner % Pesos o UF
                             # Tabla N17: Tipo Moneda del plan pactado Isapre
                             # Codigo Glosa
                             # 1 Pesos
                             # 2 UF
                             "1" if payslip.contract_id.isapre_id.codigo == '07' else "2",
                             # 79 Cotizacion Pactada
                             # Yo Pensaba payslip.contract_id.isapre_cotizacion_uf,
                             "0" if payslip.contract_id.isapre_id.codigo == '07' else payslip.contract_id.isapre_cotizacion_uf,
                             # 80 Cotizacion Obligatoria Isapre
                             "0" if payslip.contract_id.isapre_id.codigo == '07' else
                             str(float(self.get_payslip_lines_value_2(payslip, 'SALUD'))).split('.')[0],
                             # 81 Cotizacion Adicional Voluntaria
                             "0" if payslip.contract_id.isapre_id.codigo == '07' else
                             str(float(self.get_payslip_lines_value_2(payslip, 'ADISA'))).split('.')[0],
                             # 82 Monto Garantia Explicita de Salud
                             "0",
                             # 8- Datos Caja de Compensacion
                             # 83 Codigo CCAF
                             # TODO ES HACER PANTALLA CON DATOS EMPRESA
                             payslip.indicadores_id.ccaf_id.codigo if payslip.indicadores_id.ccaf_id.codigo else "00",
                             # 84 Renta Imponible CCAF
                             str(float(self.get_imponible_afp(payslip and payslip[0] or False,
                                                              self.get_payslip_lines_value_2(payslip, 'TOTIM')))).split(
                                 '.')[0] if (self.get_dias_trabajados(payslip and payslip[0] or False) > 0) else "00",
                             # 85 Creditos Personales CCAF TODO
                             self.get_payslip_lines_value_2(payslip, 'PCCAF') if self.get_payslip_lines_value_2(payslip,
                                                                                                                'PCCAF') else "0",
                             # 86 Descuento Dental CCAF
                             "0",
                             # 87 Descuentos por Leasing TODO
                             self.get_payslip_lines_value_2(payslip, 'CCAF') if self.get_payslip_lines_value_2(payslip,
                                                                                                               'CCAF') else "0"
                             # 88 Descuentos por seguro de vida TODO
                                                                                                                            "0",
                             # 89 Otros descuentos CCAF
                             "0",
                             # 90 Cotizacion a CCAF de no afiliados a Isapres
                             self.get_payslip_lines_value_2(payslip, 'CAJACOMP') if self.get_payslip_lines_value_2(
                                 payslip, 'CAJACOMP') else "0",
                             # 91 Descuento Cargas Familiares CCAF
                             "0",
                             # 92 Otros descuentos CCAF 1 (Uso Futuro)
                             "0",
                             # 93 Otros descuentos CCAF 2 (Uso Futuro)
                             "0",
                             # 94 Bonos Gobierno (Uso Futuro)
                             "0",
                             # 9- Datos Mutualidad
                             # 95 Codigo de Sucursal (Uso Futuro)
                             " ",
                             # 96 Codigo Mutualidad
                             payslip.indicadores_id.mutualidad_id.codigo if payslip.indicadores_id.mutualidad_id.codigo else "00",
                             # 97 Renta Imponible Mutual TODO Si afiliado hacer
                             self.get_imponible_mutual(payslip and payslip[0] or False,
                                                       self.get_payslip_lines_value_2(payslip, 'TOTIM')),
                             # 98 Cotizacion Accidente del Trabajo
                             str(float(self.get_payslip_lines_value_2(payslip, 'MUT'))).split('.')[
                                 0] if self.get_payslip_lines_value_2(payslip, 'MUT') else "0",
                             # 99 Codigo de Sucursal (Uso Futuro)
                             "0",
                             # 10- Datos Administradora de Seguro de Cesantia
                             self.get_imponible_seguro_cesantia(payslip and payslip[0] or False,
                                                                self.get_payslip_lines_value_2(payslip, 'TOTIM'),
                                                                self.get_payslip_lines_value_2(payslip, 'IMPLIC')),
                             # 101 Aporte Trabajador Seguro Cesantia
                             str(float(self.get_payslip_lines_value_2(payslip, 'SECE'))).split('.')[
                                 0] if self.get_payslip_lines_value_2(payslip, 'SECE') else "0",
                             # 102 Aporte Empleador Seguro Cesantia
                             str(float(self.get_payslip_lines_value_2(payslip, 'SECEEMP'))).split('.')[
                                 0] if self.get_payslip_lines_value_2(payslip, 'SECEEMP') else "0",
                             # 103 Rut Pagadora Subsidio
                             # yo pensaba rut_emp,
                             "0",
                             # 104 DV Pagadora Subsidio
                             # yo pensaba rut_emp_dv,
                             "",
                             # 105 Centro de Costos, Sucursal, Agencia
                             "0"
                             # str(float(self.get_cost_center(payslip.contract_id))).split('.')[0],
                             ]
            writer.writerow([str(l) for l in line_employee])
        self.write({'file_data': base64.encodebytes(output.getvalue().encode()),
                    'file_name': "Previred_{}{}.txt".format(self.date_to, self.company_id.display_name),
                    })

        return {
            "type": "ir.actions.do_nothing",
        }

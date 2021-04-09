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
from collections import Counter



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

    indicators_id = fields.Many2one('hr.indicadores', string='Indicadores')

    company_id = fields.Many2one('res.partner', domain=lambda self: [
        ('id', 'in', self.env['hr.employee'].sudo().search([('active', '=', True)]).mapped('address_id').mapped('id'))])

    report = fields.Binary(string='Descarge aqui =>',
                           default=lambda self: self.env['wizard.hr.payslip'].sudo().search([])[-1].report)

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
                              default=lambda self: self.env['wizard.hr.payslip'].sudo().search([])[-1].file_data)
    file_name = fields.Char('Nombre de archivo',
                            default=lambda self: self.env['wizard.hr.payslip'].sudo().search([])[-1].file_name)
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

    centralization_report_field = fields.Binary('Centralizacion',
                                                default=lambda self: self.env['wizard.hr.payslip'].sudo().search([])[
                                                    -1].centralization_report_field)

    @api.multi
    def compute_ccaf_max(self):
        max_ccaf = self.env['hr.indicadores'].search([])[-1]
        self.ccaf_max = 80 * max_ccaf.uf

    @api.multi
    def print_report_xlsx(self):
        file_name = 'temp'
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet(self.company_id.name)
        number_format=workbook.add_format({'num_format': '#,###'})
        indicadores = self.env['hr.indicadores'].sudo().search([('name', '=', f'{self.month} {self.years}')])
        if not indicadores:
            raise models.ValidationError(f'No existen datos del mes de {self.month} {self.years}')
        if indicadores.state != 'done':
            raise models.ValidationError(
                f'Los indicadores provicionales del mes de {indicadores.name} no se encuentran validados')
        row = 13
        col = 0
        payslips = self.env['hr.payslip'].sudo().search(
            [('indicadores_id', '=', indicadores.id), ('state', 'in', ['done', 'draft']),('employee_id.address_id.id','=',self.company_id.id), ('name', 'not like', 'Devolución:')])


        totals = self.env['hr.payslip.line'].sudo().search([('slip_id', 'in', payslips.mapped('id'))]).filtered(
            lambda a: a.total > 0)

        totals_result = []
        payslips = totals.mapped('slip_id')
        bold_format = workbook.add_format({'bold': True})
        worksheet.write(0, 0, self.company_id.name,bold_format)
        worksheet.write(1,0, 'PROCESO Y COMERCIALIZACION DE NUECES', bold_format)
        worksheet.write(2,0, self.company_id.street, bold_format)
        worksheet.write(3,0, self.company_id.city, bold_format)
        worksheet.write(4,0, self.company_id.country_id.name, bold_format)
        worksheet.write(5,0, self.company_id.invoice_rut, bold_format)
        worksheet.write(6,0, 'Fecha Informe : '+datetime.today().strftime('%d-%m-%Y'), bold_format)
        worksheet.write(7,0, self.month, bold_format)
        worksheet.write(8,0, 'Fichas : Todas', bold_format)
        worksheet.write(9,0, 'Area de Negocio : Todas las Areas de Negocios', bold_format)
        worksheet.write(10,0, 'Centro de Costo : Todos los Centros de Costos', bold_format)
        worksheet.write(11,0, 'Total Trabajadores : '+ str(len(payslips)), bold_format)
        for pay in payslips:
            rules = self.env['hr.salary.rule'].sudo().search([('id', 'in', totals.mapped('salary_rule_id').mapped('id'))],
                                                      order='order_number')
            col = 0

            worksheet.write(row, col, pay.employee_id.display_name)
            worksheet.write(12, 0, 'Nombre', bold_format)
            long_name = max(payslips.mapped('employee_id').mapped('display_name'), key=len)
            worksheet.set_column(row, col, len(long_name))
            col += 1
            worksheet.write(12, 1, 'Rut', bold_format)
            worksheet.write(row, col, pay.employee_id.identification_id)
            long_rut = max(payslips.mapped('employee_id').mapped('identification_id'), key=len)
            worksheet.set_column(row, col, len(long_rut))
            col += 1
            worksheet.write(12, 2, 'N° Centro de Costo', bold_format)
            if pay.account_analytic_id:
                worksheet.write(row, col, pay.account_analytic_id.code)
            elif pay.contract_id.department_id.analytic_account_id:
                worksheet.write(row, col, pay.contract_id.department_id.analytic_account_id.code)
            else:
                worksheet.write(row, col, '')
            long_const = max(
                payslips.mapped('contract_id').mapped('department_id').mapped('analytic_account_id').mapped('name'),
                key=len)
            worksheet.set_column(row, col, len(long_const))
            col += 1
            worksheet.write(12, 3, 'Centro de Costo:', bold_format)
            if pay.account_analytic_id:
                worksheet.write(row, col, pay.account_analytic_id.name)
            elif pay.contract_id.department_id.analytic_account_id:
                worksheet.write(row, col, pay.contract_id.department_id.analytic_account_id.name)
            else:
                worksheet.write(row, col, '')
            long_const = max(
                payslips.mapped('contract_id').mapped('department_id').mapped('analytic_account_id').mapped('name'),
                key=len)
            worksheet.set_column(row, col, len(long_const))
            col += 1
            worksheet.write(12, 4, 'Dias Trabajados:', bold_format)
            worksheet.write(row, col, self.get_dias_trabajados(pay))
            col += 1
            worksheet.write(12, col, 'Cant. Horas Extras', bold_format)
            worksheet.write(row, col, self.get_qty_extra_hours(payslip=pay))
            totals_result.append({col : self.get_qty_extra_hours(payslip=pay)})
            col += 1
            for rule in rules:
                if not rule.show_in_book:
                    continue
                if not totals.filtered(lambda a: a.salary_rule_id.id == rule.id):
                    continue
                if rule.code == 'HEX50':
                    worksheet.write(12, col, 'Valor Horas Extras', bold_format)
                    total_amount = self.env["hr.payslip.line"].sudo().search(
                        [("slip_id", "=", pay.id), ("salary_rule_id", "=", rule.id)]).total
                    worksheet.write(row, col, total_amount,number_format)
                    totals_result.append({col : total_amount})
                elif rule.code == 'HEXDE':
                    worksheet.write(12, col, 'Cant. Horas Descuentos', bold_format)
                    worksheet.write(row, col, self.get_qty_discount_hours(payslip=pay))
                    totals_result.append({col : self.get_qty_discount_hours(payslip=pay)})
                    col += 1
                    worksheet.write(12, col, 'Monto Horas Descuentos', bold_format)
                    total_amount = self.env["hr.payslip.line"].sudo().search(
                        [("slip_id", "=", pay.id), ("salary_rule_id", "=", rule.id)]).total
                    worksheet.write(row, col,total_amount,number_format)
                    totals_result.append({col : total_amount})
                else:
                    total_amount = self.env["hr.payslip.line"].sudo().search(
                        [("slip_id", "=", pay.id), ("salary_rule_id", "=", rule.id)]).total
                    worksheet.write(12, col, rule.name, bold_format)
                    worksheet.write(row, col,total_amount,number_format)
                    totals_result.append({col : total_amount})
                col += 1
            col = 0
            row += 1
        counter = Counter()
        for item in totals_result:
            counter.update(item)
        total_dict = dict(counter)
        worksheet.write(row, 0, 'Totales',bold_format)
        number_bold_format = workbook.add_format({'num_format': '#,###', 'bold': True})
        for k in total_dict:
            worksheet.write(row, k,total_dict[k],number_bold_format)
        col = 0
        row += 1
        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())

        file_name = 'Libro de Remuneraciones {}'.format(indicadores.name)
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': file_name,
            'datas_fname': file_name,
            'datas': file_base64
        })
        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'current',
        }
        return action

    @api.multi
    def generate_centralization(self):
        payslips = self.env['hr.payslip'].sudo().search(
            [('indicadores_id', '=', self.indicators_id.id), ('state', '=', 'done')])
        file_name = 'temp.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet('Prueba')

        format_title = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'center'
        })
        worksheet = self.set_format_title(worksheet, format_title)
        line = self.env['hr.payslip.line'].search([('slip_id', '=', payslips.mapped('id'))])
        row = 5
        col = 3
        sum_totals = []
        rule = self.env['hr.salary.rule'].sudo().search([('show_in_central', '=', True), ('category_id', '!=', 9)])
        for data in rule:
            line = self.search_data([('slip_id', 'in', payslips.mapped('id')), ('salary_rule_id', '=', data.id)])
            worksheet.write(row, col - 2, data.name)
            total = sum(line.mapped("total"))
            sum_totals.append(total)
            worksheet.write(row, col, total)
            if data.id == rule[-1].id:
                totals = sum(sum_totals)
                worksheet.write(row + 1, col, totals)
                row += 1
            else:
                row += 1
        row += 2

        sum_totals_discount = []
        discount = self.env['hr.salary.rule'].sudo().search(
            [('show_in_central', '=', True), ('category_id', '=', 9), ('is_legal', '=', True)])
        total_line = self.search_data([('slip_id', 'in', payslips.mapped('id')), (
            'salary_rule_id.code', 'in', ('APV', 'FONASA', 'SALUD', 'ADISA', 'SECE', 'PREV'))])
        sum_total_line = sum(total_line.mapped('total'))
        sum_totals_discount.append(sum_total_line)
        worksheet.write(row, col - 2, 'Imposiciones por Pagar')
        worksheet.write(row, col + 1, sum_total_line)
        row += 1
        for dis in discount:
            line = self.search_data([('slip_id', 'in', payslips.mapped('id')), ('rule_id', '=', dis.id)])
            worksheet.write(row, col - 2, dis.name)
            total = sum(line.mapped("total"))
            sum_totals_discount.append(total)
            worksheet.write(row, col + 1, total)
            if data.id == rule[-1].id:
                totals = sum(sum_totals_discount)
                worksheet.write(row + 1, col + 1, totals)
                row += 1
            else:
                row += 1

        row += 2
        another_discount = self.env['hr.salary.rule'].sudo().search(
            [('is_legal', '=', False), ('category_id', 'in', (9, 11))])
        for another_discount in another_discount:
            line = self.search_data(
                [('slip_id', 'in', payslips.mapped('id')), ('salary_rule_id', '=', another_discount.id)])
            worksheet.write(row, col - 2, another_discount.name)
            total = sum(line.mapped("total"))
            worksheet.write(row, col + 1, total)
            row += 1

        workbook.close()

        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        centralization = self.env[self._name].sudo().create({
            'centralization_report_field': file_base64
        })
        self.write({
            'centralization_report_field': centralization.centralization_report_field
        })
        return {
            'type': 'ir.actions.do_nothing'
        }

    def search_data(self, conditions):
        return self.env['hr.payslip.line'].search(conditions)

    def set_format_title(self, worksheet, format_title):
        worksheet.set_column('B:B', 68)
        worksheet.set_column('C:C', len('Centro de Costo'))
        worksheet.set_column('D:D', 32)
        worksheet.set_column('E:E', 15)
        worksheet.merge_range('B2:E2', 'Centralizacion de Remuneraciones', format_title)
        worksheet.write(3, 1, 'Descripcion', format_title)
        worksheet.write(3, 2, 'Centro de Costo', format_title)
        worksheet.write(3, 3, 'DEBE', format_title)
        worksheet.write(3, 4, 'HABER', format_title)
        return worksheet

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
    def get_qty_extra_hours(self, payslip):
        worked_days = 0
        if payslip:
            for line in payslip.input_line_ids:
                if line.code == 'HEX50':
                    worked_days = line.amount
        return worked_days

    @api.model
    def get_qty_discount_hours(self, payslip):
        worked_days = 0
        if payslip:
            for line in payslip.input_line_ids:
                if line.code == 'HEXDE':
                    worked_days = line.amount
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
        data = round(detalle.total)

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
            return str(float(round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf)))
        else:
            return str(round(float(round(TOTIM_2))))

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
        if TOTIM_2 < payslip.indicadores_id.sueldo_minimo:
            return 0
        if LIC_2 > 0:
            TOTIM = LIC
        if payslip.contract_id.pension is True:
            return 0
        elif payslip.contract_id.type_id.name == 'Sueldo Empresarial':
            return 0
        elif TOTIM_2 >= round(payslip.indicadores_id.tope_imponible_seguro_cesantia * payslip.indicadores_id.uf):
            return str(round(
                float(round(payslip.indicadores_id.tope_imponible_seguro_cesantia * payslip.indicadores_id.uf))))
        else:
            return str(round(float(round(TOTIM_2))))

    @api.model
    def get_imponible_salud(self, payslip, TOTIM):
        result = 0
        TOTAL = float(TOTIM)
        if TOTAL >= round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf):
            return str(float(round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf)))
        else:
            return str(float(round(TOTAL)))

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
    def verify_ccaf(self, TOTIM, UF, TOPE):
        if TOTIM:
            TOTIM_2 = float(TOTIM)
            if TOTIM_2 > (UF * TOPE):
                data = round(float(UF * TOPE))
                return str(data)
            else:
                return str(TOTIM)
        else:
            return "0"

    @api.multi
    def verify_ips(self, TOTIM, UF, TOPE):
        TOTIM_2 = float(TOTIM)
        if TOTIM_2 > (UF * TOPE):
            data = round(float(UF * TOPE))
            return data
        else:
            return TOTIM

    @api.multi
    def verify_quotation_afc(self, TOTIM, indicadores, contract):
        totimp = float(TOTIM)
        if contract.type_id.name == 'Plazo Fijo':
            return round(totimp * indicadores.contrato_plazo_fijo_empleador / 100)
        elif contract.type_id.name == 'Plazo Indefinido':
            return round(totimp * indicadores.contrato_plazo_indefinido_empleador / 100)
        else:
            return 0

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
        payslip_recs = payslip_model.sudo().search([('date_from', '=', self.date_from),
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
            payslip_line_recs = payslip_line_model.sudo().search([('slip_id', '=', payslip.id)])
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
                             str(round(self.get_dias_trabajados(payslip and payslip[0] or False))),
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
                                                                self.get_payslip_lines_value_2(payslip,
                                                                                               'TOTIM')) if not payslip.contract_id.data_id else
                             payslip.contract_id.data_id.name.split(' ')[1],
                             # 19 NCargas Simples
                             payslip.contract_id.carga_familiar,
                             payslip.contract_id.carga_familiar_maternal,
                             payslip.contract_id.carga_familiar_invalida,
                             # 22 Asignacion Familiar
                             self.get_payslip_lines_value_2(payslip, 'ASIGFAM') if self.get_payslip_lines_value_2(
                                 payslip, 'ASIGFAM') else "0",
                             # ASIGNACION FAMILIAR RETROACTIVA
                             self.get_payslip_lines_value_2(payslip, 'ASFRETRO') if self.get_payslip_lines_value_2(
                                 payslip, 'ASFRETRO') else "0",
                             # Refloategro Cargas Familiares
                             "0",
                             # 25 Solicitud Trabajador Joven TODO SUBSIDIO JOVEN
                             "N",
                             # 26
                             payslip.contract_id.afp_id.codigo if payslip.contract_id.afp_id.codigo else "00",
                             # 27
                             str(round(float(self.get_imponible_afp_2(payslip and payslip[0] or False,
                                                                      self.get_payslip_lines_value_2(payslip, 'TOTIM'),
                                                                      self.get_payslip_lines_value_2(payslip,
                                                                                                     'IMPLIC'))))),
                             # AFP SIS APV 0 0 0 0 0 0
                             # 28
                             str(round(float(self.get_payslip_lines_value_2(payslip, 'PREV')))),
                             str(round(float(self.get_payslip_lines_value_2(payslip, 'SIS')))),
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
                             # 3- Datos Ahorro Previsional Voluntario Indiidual
                             ## 40 Código de lav Institución APVI
                             payslip.contract_id.apv_id.codigo if self.get_payslip_lines_value_2(payslip,
                                                                                                 'APV') != "0" else "0",
                             # 41 Numero de Contrato APVI Strinng
                             "0",
                             # 42 Forma de Pago Ahorro
                             payslip.contract_id.forma_pago_apv if self.get_payslip_lines_value_2(payslip,
                                                                                                  'APV') else "0",
                             # 43 Cotización APVI 9(8) Monto en $ de la Cotización APVI
                             str(round(float(self.get_payslip_lines_value_2(payslip, 'APV')))) if str(
                                 round(float(self.get_payslip_lines_value_2(payslip, 'APV')))) else "0",
                             # 44 Cotizacion Depositos
                             " ",
                             # 45 Codigo Institucion Autorizada APVC
                             "0",
                             # 46 Numero de Contrato APVC TODO
                             "0",
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
                             # 54 Nombres Vol
                             " ",
                             # 55 Tabla N°7: Movimiento de Personal
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

                             "0",
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
                             self.verify_ips(self.get_payslip_lines_value_2(payslip, 'TOTIM'),
                                             payslip.indicadores_id.uf,
                                             payslip.indicadores_id.tope_imponible_ips) if self.get_payslip_lines_value_2(
                                 payslip,
                                 'TOTIM') else "0",
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
                             self.get_payslip_lines_value_2(payslip,
                                                            'FONASA') if payslip.contract_id.isapre_id.codigo == '07' else "0",

                             # 71 Cotizacion Acc. Trabajo (ISL)
                             str(round(float(
                                 self.get_payslip_lines_value_2(payslip, 'ISL')))) if self.get_payslip_lines_value_2(
                                 payslip, 'ISL') else "0",

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
                             str(round(float(self.get_payslip_lines_value_2(payslip, 'SALUD')))),
                             # 81 Cotizacion Adicional Voluntaria
                             "0" if payslip.contract_id.isapre_id.codigo == '07' else
                             str(round(float(self.get_payslip_lines_value_2(payslip, 'ADISA')))),
                             # 82 Monto Garantia Explicita de Salud
                             "0",
                             # 8- Datos Caja de Compensacion
                             # 83 Codigo CCAF
                             # TODO ES HACER PANTALLA CON DATOS EMPRESA
                             payslip.indicadores_id.ccaf_id.codigo if payslip.indicadores_id.ccaf_id.codigo else "00",
                             # 84 Renta Imponible CCAF
                             self.verify_ccaf(self.get_payslip_lines_value_2(payslip, 'TOTIM'),
                                              payslip.indicadores_id.uf,
                                              payslip.indicadores_id.tope_imponible_afp) if self.get_payslip_lines_value_2(
                                 payslip,
                                 'TOTIM') else "0",
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
                             "0",
                             # 96 Codigo Mutualidad
                             payslip.indicadores_id.mutualidad_id.codigo if payslip.indicadores_id.mutualidad_id.codigo else "00",
                             # 97 Renta Imponible Mutual TODO Si afiliado hacer
                             self.get_imponible_mutual(payslip and payslip[0] or False,
                                                       self.get_payslip_lines_value_2(payslip, 'TOTIM')),
                             # 98 Cotizacion Accidente del Trabajo
                             str(round(float(
                                 self.get_payslip_lines_value_2(payslip, 'MUT')))) if self.get_payslip_lines_value_2(
                                 payslip, 'MUT') else "0",
                             # 99 Codigo de Sucursal (Uso Futuro)
                             "0",
                             # 10- Datos Administradora de Seguro de Cesantia
                             self.get_imponible_seguro_cesantia(payslip and payslip[0] or False,
                                                                self.get_payslip_lines_value_2(payslip, 'TOTIM'),
                                                                self.get_payslip_lines_value_2(payslip, 'IMPLIC')),
                             # 101 Aporte Trabajador Seguro Cesantia
                             str(round(float(
                                 self.get_payslip_lines_value_2(payslip, 'SECE')))) if self.get_payslip_lines_value_2(
                                 payslip, 'SECE') else "0",
                             # 102 Aporte Empleador Seguro Cesantia
                             str(self.verify_quotation_afc(
                                 self.get_imponible_seguro_cesantia(payslip and payslip[0] or False,
                                                                    self.get_payslip_lines_value_2(payslip, 'TOTIM'),
                                                                    self.get_payslip_lines_value_2(payslip, 'IMPLIC')),
                                 payslip.indicadores_id, payslip.contract_id)),
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

        # registrar en ir.attachment
        file_name = "Previred_{}{}.txt".format(self.date_to,
                                               self.company_id.display_name.replace('.', ''))
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': file_name,
            'datas_fname': file_name,
            'datas': base64.encodebytes(output.getvalue().encode())
        })

        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'self',
        }
        return action

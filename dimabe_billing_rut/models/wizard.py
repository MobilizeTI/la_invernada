from odoo import api, fields, models
from odoo.tools.misc import xlwt
import io
import xlsxwriter
import base64


class WizardHrPaySlip(models.TransientModel):
    _name = "wizard.hr.payslip"
    _description = 'XLSX Report'

    company_id = fields.Many2one('res.company', 'Compañia')

    report = fields.Binary(default=lambda self: self.env['wizard.hr.payslip'].search([])[-1].report)

    month = fields.Selection(
        [('Enero', 'Enero'), ('Febrero', 'Febrero'), ('Marzo', 'Marzo'), ('Abril', 'Abril'), ('Mayo', 'Mayo'),
         ('Junio', 'Junio'), ('Julio', 'Julio'),
         ('Agosto', 'Agosto'), ('Septiembre', 'Septiembre'), ('Octubre', 'Octubre'), ('Noviembre', 'Noviembre'),
         ('Diciembre', 'Diciembre'), ], string="Mes")

    years = fields.Selection([('2019', '2019'), ('2020', '2020'), ('2021', '2021')], string="Año")

    all = fields.Boolean('Todos las compañias')

    @api.multi
    def print_report_xlsx(self):
        file_name = 'temp'
        workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
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
        worksheet.merge_range(
            "B2:E2", "Informe: Libro de Remuneraciones", merge_format_title)
        worksheet.merge_range("B3:E3", "Mes a procesar : {}".format(
            '{} {}'.format(self.month,self.years)), merge_format_title)
        worksheet.merge_range('B4:E4', "Compañia : {}".format(
            self.company_id.name
        ), merge_format_title)

        employees = self.env['hr.employee'].search([('address_id', '=', self.company_id.partner_id.id)])
        if len(employees) == 0:
            raise models.ValidationError('No existen empleados creados con este empresa,por favor verificar la direccion de trabajado del empleado')
        row = 8

        payslips = self.env['hr.payslip'].search([('indicadores_id', '=',indicadores_id.id)])
        raise models.ValidationError(map(chr, range(97, 123)))
        for emp in employees:

            row += 1
        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        self.write({'report': file_base64})
        return {
            "type": "ir.actions.do_nothing",
        }


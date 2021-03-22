from odoo import fields, models, api
import xlsxwriter
import base64


class ProcessReport(models.TransientModel):
    _name = 'process.report.xlsx'

    process_selection = fields.Selection(
        [('ncc', 'Informe de Proceso Envasado NCC'), ('laser', 'Informe de Proceso Mecanico/Laser'),
         ('manual', 'Informe de Proceso Partido Manual Calidad'), ('nsc', 'Informe de Proceso Envasado NSC'),
         ('calibrate', 'Informe de Proceso Calibrado'), ('washed', 'Informe de Proceso Lavado'),
         ('re-laser', 'Informe de Re-Proceso Descarte laser'),
         ('service_ncc', 'Informe de Proceso Envasado NCC Servicio'),
         ('service_nsc', 'Informe de Proceso Envasado NSC Servicio'),
         ('service_calibrate', 'Informe de Proceso Calibrado Servicio'),
         ('service_washed', 'Informe de Proceso Lavado Servicio'),
         ('service_laser', 'Informe de Proceso Mecanico/Laser Servicio'),
         ('service_re_laser', 'Informe de Re-Proceso Descarte Laser Servicio'),
         ('service_manual', 'Informe de Proceso Manuel Calidad Servicio')
         ])

    @api.multi
    def generate_xlsx(self):
        if self.process_selection == 'ncc':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '320-PENCC')])
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': dict_data['file_name'],
            'datas_fname': dict_data['file_name'],
            'datas': dict_data['base64']
        })

        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'new',
        }
        return action

    def generate_xlsx_process(self, query, process_name):
        file_name = 'process_name.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        text_format = workbook.add_format({
            'text_wrap': True
        })
        sheet = workbook.add_worksheet(process_name)
        processes = self.env['mrp.workorder'].sudo().search(query)
        for process in processes:
            sheet.merge_range(0, 0, 8, 8, 'Resumen de Entrada')
            sheet.merge_range(9, 9, 19, 19, 'Resumen de Salida')

        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        report_name = f'Informe de Proceso {process_name}'
        return {'file_name': report_name, 'base64': file_base64}

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
            dict_data = self.generate_xlsx_process([('workcenter_id.name', '=', '320-Proceso Envasado NCC')],
                                                   'Proceso NCC')
        if self.process_selection == 'laser':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '400-PPM')],
                                                   'Proceso Partido Mecanico/Laser')
        if self.process_selection == 'manual':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '500-PPMC')],
                                                   'Proceso Partido Manual Calidad')
        if self.process_selection == 'nsc':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '420-PENSC')], 'Proceso NSC')
        if self.process_selection == 'calibrate':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '300-PC')], 'Proceso Calibrado')
        if self.process_selection == 'washed':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '310-PL')], 'Proceso Lavado')
        if self.process_selection == 're-laser':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '410-PDL')],
                                                   'Re-Proceso Descarte Láser')
        if self.process_selection == 'service_ncc':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '860-PENCCS')],
                                                   'Proceso Envasado NCC Servicio')
        if self.process_selection == 'service_nsc':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '890-PENSCS')],
                                                   'Proceso Envasado NSC Servicio')
        if self.process_selection == 'service_calibrate':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '840-PCS')],
                                                   'Proceso Calibrado Servicio')
        if self.process_selection == 'service_washed':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '850-PLS')], 'Proceso Lavado Servicio')
        if self.process_selection == 'service_laser':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '870-PPMS')],
                                                   'Proceso Partido Mecanico/Laser Servicio')
        if self.process_selection == 'service_re_laser':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '880-PDLS')],
                                                   'Re-Proceso Descarte Láser Servicio')
        if self.process_selection == 'service_manual':
            dict_data = self.generate_xlsx_process([('workcenter_id.code', '=', '870-PPMS')],
                                                   'Proceso Partido Manual Calidad Servicio')

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
        file_name = 'temp_report.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        text_format = workbook.add_format({
            'text_wrap': True
        })
        sheet = workbook.add_worksheet(process_name)
        processes = self.env['mrp.workorder'].search(query)
        models._logger.error(f'Process len {len(processes)} {processes}')
        row = 0
        col = 0

        titles = ['Proceso Entrada', 'Pedido', 'Fecha Produccion', 'Lote', 'Serie', 'Productor', 'Producto', 'Variedad',
                  'Peso', 'Proceso Salida', 'Pedido', 'Fecha Produccion', 'Productor', 'Producto', 'Variedad', 'Pallet',
                  'Lote', 'Serie', 'Peso Real']
        for title in titles:
            sheet.write(row, col, title, text_format)
            col += 1
        col = 1
        row += 1
        for process in processes:
            sheet.write(row,col,process.production_id.name)

        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        report_name = f'Informe de Proceso {process_name}'
        return {'file_name': report_name, 'base64': file_base64}

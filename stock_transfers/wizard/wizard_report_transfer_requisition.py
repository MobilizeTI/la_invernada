
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

class wizard_report_transfer_requisition(models.TransientModel):

    _name = 'wizard.report.transfer.requisition'
    _description = 'Asistente para filtrar reporte de tranferencias'
    
    @api.model
    def get_default_start_date(self):
        util_model = self.env['odoo.utils']
        return util_model._change_time_zone((datetime.now() + relativedelta(day=1, minute=0, second=0, hour=0))).strftime(DTF)
    
    
    location_ids = fields.Many2many('stock.location', 
        'wizard_transfer_requisition_location_rel', 'wizard_id', 'location_id', 'Bodegas Destino',)
    location_source_ids = fields.Many2many('stock.location', 
        'wizard_transfer_requisition_location_source_rel', 'wizard_id', 'location_id', 'Bodegas Origen')
    user_ids = fields.Many2many('res.users', 
        'wizard_transfer_requisition_users_rel', 'wizard_id', 'user_id', 'Usuarios')
    product_ids = fields.Many2many('product.product', 
        'wizard_transfer_requisition_product_rel', 'wizard_id', 'product_id', 'Productos')
    date_start = fields.Datetime('Desde', default=get_default_start_date)
    date_end = fields.Datetime('Hasta')
    to_process = fields.Boolean('Solo datos marcados "procesar"?')
    report_name = fields.Selection([
        ('transfer_requisition_report_ods','Archivo Excel(.xls)'),
        ('transfer_requisition_report_pdf','Archivo PDF(.pdf)'),
        ],    string='Formato del reporte', index=True, readonly=False, default='transfer_requisition_report_ods')
    
    @api.one
    def get_report_data(self):
        ctx = self.env.context.copy()
        ctx['date_start'] = self.date_start
        ctx['date_end'] = self.date_end
        ctx['location_ids'] = self.location_ids.ids
        ctx['location_source_ids'] = self.location_source_ids.ids
        ctx['product_ids'] = self.product_ids.ids
        ctx['user_ids'] = self.user_ids.ids
        ctx['to_process'] = self.to_process
        return self.env['transfer.requisition'].with_context(ctx).MakeReportTransfer()
    
    @api.multi
    def action_print_report(self):
        ctx = self.env.context.copy()
        ctx['date_start'] = self.date_start
        ctx['date_end'] = self.date_end
        ctx['location_ids'] = self.location_ids.ids
        ctx['location_source_ids'] = self.location_source_ids.ids
        ctx['product_ids'] = self.product_ids.ids
        ctx['user_ids'] =  self.user_ids.ids
        ctx['to_process'] = self.to_process
        if self.report_name == 'transfer_requisition_report_ods':
            res = {'type': 'ir.actions.act_url',
                   'url': '/download/saveas?model=%(model)s&record_id=%(record_id)s&method=%(method)s&filename=%(filename)s' % {
                        'filename': 'Transferencias.xlsx',
                        'model': self._name,
                        'record_id': self.id,
                        'method': 'get_report_data',
                        },
                   'target': 'new',
                   }
        else:
            company = self.env.user.company_id
            ctx['active_ids'] = [company.id]
            ctx['active_id'] = company.id
            ctx['active_model'] = 'res.company'
            res = self.env['report'].with_context(ctx).get_action(company, 'stock_transfers.report_transfer_requisition_list', {})
        return res
    
wizard_report_transfer_requisition()
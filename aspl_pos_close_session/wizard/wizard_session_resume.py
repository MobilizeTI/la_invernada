from dateutil.relativedelta import relativedelta

from odoo import models, api, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

class WizardSessionResume(models.TransientModel):
    _name = 'wizard.session.resume'
    _description = 'Asistente para generar Resumen de caja'
    
    @api.model
    def get_default_start_date(self):
        util_model = self.env['odoo.utils']
        return util_model._change_time_zone((fields.Datetime.context_timestamp(self, fields.Datetime.now()) + relativedelta(minute=0, second=0, hour=0))).strftime(DTF)
    
    @api.model
    def get_default_end_date(self):
        util_model = self.env['odoo.utils']
        return util_model._change_time_zone((fields.Datetime.context_timestamp(self, fields.Datetime.now()) + relativedelta(hour=23, minute=59, second=59))).strftime(DTF)
    
    @api.model
    def get_default_warehouse(self):
        return self.env['stock.warehouse'].search([])

    date_from = fields.Datetime('Desde', default=get_default_start_date)
    date_to = fields.Datetime('Hasta', default=get_default_end_date)
    warehouse_ids = fields.Many2many('stock.warehouse', 
        'wizard_session_resume_warehouse_rel', 'wizard_id', 'warehouse_id', 'Tiendas',
        default=get_default_warehouse)

    @api.multi
    def action_print(self):
        self.ensure_one()
        warehouse_recs = self.warehouse_ids if self.warehouse_ids else self.get_default_warehouse()
        data = self.read(['date_from', 'date_to', 'warehouse_ids'])[0]
        datas = {
            'ids': warehouse_recs.ids,
            'model': 'stock.warehouse',
            'form': data
        }
        return self.env.ref('aspl_pos_close_session.pos_session_resume_report').report_action(warehouse_recs, datas)

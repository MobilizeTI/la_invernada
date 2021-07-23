
from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning, ValidationError

class wizard_received_transfer_requisition(models.TransientModel):

    _name = 'wizard.received.transfer.requisition'
    _description = 'Recibir requisición de transferencia'
    
    requisition_id = fields.Many2one('transfer.requisition', 'Solicitud de transferencia')
    line_normal_ids = fields.One2many('wizard.received.transfer.requisition.line.normal', 'wizard_id', 'Recibidas completamente', 
        save_readonly=True)
    line_diff_ids = fields.One2many('wizard.received.transfer.requisition.line', 'wizard_id', 'Lineas a Revisar', 
        save_readonly=True, domain=[('process_type', '=', 'diff')])
    
    @api.model
    def default_get(self, fields_list):
        values = super(wizard_received_transfer_requisition, self).default_get(fields_list)
        requisition_model = self.env['transfer.requisition']
        ids = self.env.context.get('active_ids',[])
        active_model = self.env.context.get('active_model','')
        if active_model == requisition_model._name and ids:
            requisition = requisition_model.browse(ids[0])
            line_normal_ids_temp, line_diff_ids = requisition_model._get_lines_changed(requisition, 'qty_process','qty_received')
            line_normal_ids = []
            for line in line_normal_ids_temp:
                line_normal_ids.append({
                    'line_id': line['line_id'],
                    'product_id': line['product_id'],
                    'qty_process': line['qty_process'],
                    'qty_received': line['qty_received'],
                })
            values['line_normal_ids'] = [(0, 0, vals) for vals in line_normal_ids]
            values['line_diff_ids'] = [(0, 0, vals) for vals in line_diff_ids]
            values['requisition_id'] = requisition.id
        return values
    
    @api.multi
    def action_process(self):
        reason_model = self.env['transfer.requisition.reason']
        for line in self.line_diff_ids:
            if line.process_type == 'diff':
                if line.process_mode:
                    line.line_id.write({'process_mode': line.process_mode})
                if not line.note:
                    raise Warning(_("Debe Ingresar la razon por la que hay diferencias en los productos recibidos"))
                reason_model.create({
                    'product_id': line.product_id.id,
                    'line_id': line.line_id.id,
                    'name': line.note,
                    'requisition_id': self.requisition_id.id, 
                })
        #una vez generada la copia, enviar a recibir la solicitud actual
        self.requisition_id._action_receive()
        return {'type': 'ir.actions.act_window_close'}
    
wizard_received_transfer_requisition()

class wizard_received_transfer_requisition_line(models.TransientModel):

    _name = 'wizard.received.transfer.requisition.line'
    _description = 'Lineas de requisición de transferencia'
    _order = 'product_id'
    
    wizard_id = fields.Many2one('wizard.received.transfer.requisition', 'Wizard')
    line_id = fields.Many2one('transfer.requisition.line', 'Linea relacionada', save_readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', save_readonly=True)
    qty_process = fields.Float('Solicitada', digits=dp.get_precision('Account'), save_readonly=True)
    qty_received = fields.Float('Recibida', digits=dp.get_precision('Account'), save_readonly=True)
    qty_diff = fields.Float('Diferencia', digits=dp.get_precision('Account'), save_readonly=True)
    note = fields.Char('Razón', size=64, required=False)
    # campo para saber si la linea se esta recibiendo con las cantidades solicitadas o hay un cambio en la cantidad
    process_type = fields.Selection([
        ('normal', 'Normal'),
        ('diff', 'Diferencia'),
        ],    string='Tipo de Recepcion', index=True, readonly=True, save_readonly=True)
    process_mode = fields.Selection([
        ('perdida','Pérdida'),
        ('robo','Robo'),
        ('deterioro','Deterioro'),
        ('ingreso_extra','Ingresos Extra'),
        ],    string='Diferencias dadas por', index=True, readonly=False, save_readonly=True, default = 'deterioro')

wizard_received_transfer_requisition_line()

class wizard_received_transfer_requisition_line_normal(models.TransientModel):

    _name = 'wizard.received.transfer.requisition.line.normal'
    _description = 'Lineas de requisición de transferencia a recibir'
    _order = 'product_id'
    
    wizard_id = fields.Many2one('wizard.received.transfer.requisition', 'Wizard')
    line_id = fields.Many2one('transfer.requisition.line', 'Linea relacionada', save_readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', save_readonly=True)
    qty_process = fields.Float('Solicitada', digits=dp.get_precision('Account'), save_readonly=True)
    qty_received = fields.Float('Recibida', digits=dp.get_precision('Account'), save_readonly=True)
    
wizard_received_transfer_requisition_line_normal()

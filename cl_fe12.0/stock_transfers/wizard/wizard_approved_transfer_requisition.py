
from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class wizard_approved_transfer_requisition(models.TransientModel):

    _name = 'wizard.approved.transfer.requisition'
    _description = 'Aprobar requisición de transferencia'
    
    requisition_id = fields.Many2one('transfer.requisition', 'Solicitud de transferencia')
    line_normal_ids = fields.One2many('wizard.approved.transfer.requisition.line', 'wizard_id', 'Aprobadas Correctamente', save_readonly=True, 
        domain=[('process_type', '=', 'normal')])
    line_diff_ids = fields.One2many('wizard.approved.transfer.requisition.line', 'wizard_id', 'Lineas a Revisar', save_readonly=True, 
        domain=[('process_type', '=', 'diff')])
    process_mode = fields.Selection([
        ('close', 'Cantidades aprobadas y cerrar solicitud'),
        ('copy', 'Cantidades aprobadas y nueva solicitud por diferencias'),
    ],    string='Modo de Aprobar', index=True)
    
    @api.model
    def default_get(self, fields_list):
        values = super(wizard_approved_transfer_requisition, self).default_get(fields_list)
        requisition_model = self.env['transfer.requisition']
        ids = self.env.context.get('active_ids',[])
        active_model = self.env.context.get('active_model','')
        if active_model == requisition_model._name and ids:
            requisition = requisition_model.browse(ids[0])
            line_normal_ids, line_diff_ids = requisition_model._get_lines_changed(requisition)
            values['line_normal_ids'] = [(0, 0, vals) for vals in line_normal_ids]
            values['line_diff_ids'] = [(0, 0, vals) for vals in line_diff_ids]
            values['requisition_id'] = requisition.id
        return values
    
    @api.multi
    def action_process(self):
        new_line_ids = []
        if self.process_mode == 'copy':
            #si tengo que generar otra solicitud con las restantes
            default_vals = {'backorder_id': self.requisition_id.id}
            new_requisition = self.requisition_id.copy(default_vals)
            for line in self.line_diff_ids:
                #modificar la cantidad pedida, dejar solo la cantidad aprobada
                #si la cantidad aprobada es mayor a lo solicitado, pasarlo a la linea, para que sea eso lo que deba recibir
#                 line.line_id.write({'product_qty': line.qty_process,
#                                     }, context=context)
                if line.qty_diff > 0.0:
                    continue
                #crear una copia de las lineas con la cantidad restante
                default_vals = {
                    'requisition_id': new_requisition.id,
                    'product_qty': abs(line.qty_diff),
                    'qty_process': 0.0,
                    'qty_received': 0.0,
                    'to_process': False,
                }
                new_line_id = line.line_id.copy(default_vals)
                new_line_ids.append(new_line_id)
            if new_requisition:
                if new_line_ids:
                    #dejar en estado solicitado el nuevo registro
                    new_requisition.action_request()
                    message = _("Se creo una transferencia adicional por la diferencia solicitada y no aprobada: <a href=# data-oe-model=transfer.requisition data-oe-id=%d>%s</a>") % (new_requisition.id, new_requisition.display_name)
                    self.requisition_id.message_post(body=message)
                else:
                    #si no se crearon lineas eliminar la cabecera
                    new_requisition.unlink()
        #una vez generada la copia, enviar a aprobar la solicitud actual
        res = self.requisition_id._action_approved()
        if isinstance(res, bool):
            res = {'type': 'ir.actions.act_window_close'}
        return res
    
wizard_approved_transfer_requisition()


class wizard_approved_transfer_requisition_line(models.TransientModel):

    _name = 'wizard.approved.transfer.requisition.line'
    _description = 'Lineas de requisición de transferencia'
    _order = 'process_type,product_id'
    
    wizard_id = fields.Many2one('wizard.approved.transfer.requisition', 'Wizard')
    line_id = fields.Many2one('transfer.requisition.line', 'Linea relacionada', required=False, save_readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', required=False, save_readonly=True)
    product_qty = fields.Float('Cantidad Solicitada', digits=dp.get_precision('Account'), save_readonly=True)
    qty_process = fields.Float('Cantidad Aprobada', digits=dp.get_precision('Account'), save_readonly=True)
    qty_diff = fields.Float('Diferencia de cantidades', digits=dp.get_precision('Account'), save_readonly=True)
    # campo para saber si la linea se esta aprobando con las cantidades solicitadas o hay un cambio en la cantidad
    process_type = fields.Selection([
        ('normal', 'Normal'),
        ('diff', 'Diferencia'),
        ],    string='Tipo de Proceso', index=True, readonly=True)
    
wizard_approved_transfer_requisition_line()

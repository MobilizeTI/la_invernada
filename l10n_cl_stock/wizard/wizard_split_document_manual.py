from odoo import models, api, fields


class WizardSplitDocumentManual(models.TransientModel):
    _inherit = 'wizard.split.document.manual'

    @api.model
    def _split_remision_document(self, picking):
        picking_ids = []
        aditional_picking_id = False
        picking_model = self.env['stock.picking']
        picking_split_id = picking.id
        while picking_split_id:
            picking_split_id, aditional_picking_id = picking_model.split_delivery(picking_split_id)
            if picking_split_id:
                picking_ids.append(picking_split_id)
            if aditional_picking_id:
                picking_ids.append(aditional_picking_id)
        return picking_ids
    
    @api.multi
    def _action_split_document(self, active_model, active_ids):
        util_model = self.env['odoo.utils']
        picking_model = self.env['stock.picking']
        if active_model != picking_model._name:
            return super(WizardSplitDocumentManual, self)._action_split_document(active_model, active_ids)
        #**********************************
        #PROCESO PARA DIVIDIR GUIAS DE REMISION
        #**********************************
        picking_ids = []
        picking = picking_model.browse(active_ids[0])
        picking_ids.extend(self._split_remision_document(picking))
        id_xml = 'stock.action_picking_tree_all'
        ctx = self.env.context.copy()
        ctx['active_model'] = active_model
        ctx['active_ids'] = picking_ids
        ctx['active_id'] = picking_ids and picking_ids[0] or False
        result = util_model.with_context(ctx).show_action(id_xml, [('id', 'in', picking_ids)])
        return result

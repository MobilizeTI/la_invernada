from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self.env.context.get('filter_picking_type_from_invoice'):
            if self.env.context.get('filter_picking_type_from_invoice') in ('in_invoice', 'out_refund'):
                args.append(('code','=','incoming'))
            else:
                args.append(('code','=','outgoing'))
        return super(StockPickingType, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
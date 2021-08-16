from odoo import models, api, fields


class ReportPosPayment(models.Model):
    _inherit = 'report.pos.payment'
    _auto = False
    
    warehouse_id = fields.Many2one('stock.warehouse', 'Tienda', readonly=True)
    payment_ref = fields.Char('Codigo de autorizacion', readonly=True)
    document_class_id = fields.Many2one('sii.document_class', string='Tipo de Documento', readonly=True)
    is_cash_in = fields.Boolean('Es Ingreso extra?', readonly=True)
    is_cash_out = fields.Boolean('Es Egreso extra?', readonly=True)
    is_adjustment = fields.Boolean('Es ajuste de cierre?', readonly=True)
    pos_deposit_id = fields.Many2one('pos.deposit', 'Deposito del POS')


    def _select(self):
        selectr_str = super(ReportPosPayment, self)._select()
        selectr_str += """
            , c.warehouse_id AS warehouse_id,
            po.document_class_id,
            l.payment_ref,
            l.is_cash_in,
            l.is_cash_out,
            l.is_adjustment,
            l.pos_deposit_id
        """
        return selectr_str
    
    def _group_by(self):
        group_by_str = super(ReportPosPayment, self)._group_by()
        group_by_str += """
            ,c.warehouse_id, po.document_class_id, l.payment_ref, l.is_cash_in, l.is_cash_out, l.is_adjustment, l.pos_deposit_id
        """
        return group_by_str

    @api.model
    def _get_extra_domain(self):
        user_model = self.env['res.users']
        domain = []
        warehouse_ids = []
        if not user_model.has_group('point_of_sale.group_pos_manager'):
            warehouse_ids = user_model.get_all_warehouse().ids
            if warehouse_ids:
                domain.append(('warehouse_id','in', warehouse_ids))
        return domain
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        args.extend(self._get_extra_domain())
        res = super(ReportPosPayment, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
        return res
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain.extend(self._get_extra_domain())
        res = super(ReportPosPayment, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res

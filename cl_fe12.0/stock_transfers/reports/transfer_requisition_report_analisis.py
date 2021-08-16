from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo import tools


class TransferRequisitionAnalisis(models.Model):
    _name = 'transfer.requisition.analisis'
    _description = 'Analisis de Transferencias'
    _rec_name = 'product_id' 
    _auto = False
    
    process_date = fields.Datetime('Fecha para Proceso', readonly=True)
    requisition_date = fields.Datetime('Fecha de Solicitud', readonly=True)
    requisition_uid = fields.Many2one('res.users', 'Solicitado por', readonly=True)
    approved_date = fields.Datetime('Fecha de Aprobación', readonly=True)
    approved_uid = fields.Many2one('res.users', 'Aprobado por', readonly=True)
    received_date = fields.Datetime('Fecha de Recepción', readonly=True)
    received_uid = fields.Many2one('res.users', 'Recibido por', readonly=True)
    transfer_id = fields.Many2one('transfer.requisition', '# de Transferencia', readonly=True)
    backorder_id = fields.Many2one('transfer.requisition', 'Solicitud Anterior', readonly=True)
    warehouse_origin_id = fields.Many2one('stock.warehouse', 'Tienda Origen', readonly=True)
    warehouse_dest_id = fields.Many2one('stock.warehouse', 'Tienda Destino', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('request', 'Solicitado'),
        ('approved', 'Aprobado/Despachado'),
        ('process', 'Recibido'),
        ('done', 'Realizado'),
        ('cancel', 'Cancelado'),
        ],    string='Estado', index=True, readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', readonly=True)
    category_id = fields.Many2one('product.category', 'Categoria', readonly=True)
    product_qty = fields.Float('Cantidad Solicitada', digits=dp.get_precision('Product Unit of Measure'), group_operator="sum", readonly=True)
    qty_process = fields.Float('Cantidad Despachada', digits=dp.get_precision('Product Unit of Measure'), group_operator="sum", readonly=True)
    qty_remaining = fields.Float('Cantidad Faltante', digits=dp.get_precision('Product Unit of Measure'), group_operator="sum", readonly=True)
    qty_received = fields.Float('Cantidad Recibida', digits=dp.get_precision('Product Unit of Measure'), group_operator="sum", readonly=True)
    uom_id = fields.Many2one('uom.uom', 'UdM', readonly=True)
    to_process = fields.Boolean('A procesar?', readonly=True)
    
    def _select(self):
        select_str = """
            l.id,
            t.id AS transfer_id,
            COALESCE(t.process_date, t.requisition_date) AS process_date,
            t.requisition_date,
            t.approved_date,
            t.received_date,
            t.requisition_uid,
            t.approved_uid,
            t.received_uid,
            t.backorder_id,
            t.company_id,
            spt_ori.warehouse_id AS warehouse_origin_id,
            spt_dest.warehouse_id AS warehouse_dest_id,
            pt.categ_id AS category_id,
            l.product_id,
            COALESCE(l.product_qty, 0) AS product_qty,
            COALESCE(l.qty_process, 0) AS qty_process,
            COALESCE(l.qty_received, 0) AS qty_received,
            COALESCE(l.qty_process, 0) - COALESCE(l.qty_received, 0) AS qty_remaining,
            l.uom_id,
            l.to_process,
            t.state
        """
        return select_str
    
    def _from(self):
        from_str = """
            transfer_requisition_line l
            LEFT JOIN transfer_requisition t ON (t.id = l.requisition_id)
            LEFT JOIN product_product pp ON (pp.id = l.product_id)
            LEFT JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
            LEFT JOIN stock_picking_type spt_ori ON (spt_ori.id = t.picking_type_origin_id)
            LEFT JOIN stock_picking_type spt_dest ON (spt_dest.id = t.picking_type_dest_id)
            """
        return from_str
        
    def _where_str(self):
        where_str = """
            WHERE t.state NOT IN ('draft','cancel')
        """
        return where_str
    
    def _group_by(self):
        group_by_str = """
        """
        return group_by_str
    
    @api.model_cr
    def init(self):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT %s 
            FROM %s
            %s %s
        )""" % (self._table, self._select(), self._from(), self._where_str(), self._group_by()))

from odoo import models, fields

def generate_purchase_book_pdf(self, cr, uid, ids, context=None):
    datas = {}
    if context is None:
        context = {}
    data = self.read(cr, uid, ids)[0]
    datas = {
                 'ids': [],
                 'model': 'object.object',
                 'form': data
    }
    return {'type': 'ir.actions.report.xml', 'report_name': 'Reporte libro de Compras', 'datas': datas}


def generate_sale_book_pdf(self, cr, uid, ids, context=None):
    datas = {}
    if context is None:
        context = {}
    data = self.read(cr, uid, ids)[0]
    datas = {
                 'ids': [],
                 'model': 'object.object',
                 'form': data
    }
    return {'type': 'ir.actions.report.xml', 'report_name': 'Reporte libro de Ventas', 'datas': datas}
from odoo import http, models
from odoo.http import request
import logging
from datetime import date, timedelta
import werkzeug


class StockPickingController(http.Controller):

    @http.route('/api/stock_pickings', type='json', methods=['GET'], auth='token', cors='*')
    def get_stock_pickings(self, sinceDate=None):
        date_to_search = sinceDate or (date.today() - timedelta(days=7))
        result = request.env['stock.picking'].search([('write_date','>', date_to_search)])
        data = []
        if result:
            for res in result:
                if res.partner_id.id:
                    kgs = 0
                    if res.production_net_weight.is_integer():
                        kgs = int(res.production_net_weight)
                    data.append({
                        'ProducerCode': res.partner_id.id,
                        'ProducerName': res.partner_id.name,
                        'VarietyName': res.get_mp_move().product_id.get_variety(),
                        'LotNumber': res.name,
                        'DispatchGuideNumber': res.guide_number,
                        'ReceptionDate': res.scheduled_date or res.write_date,
                        'ReceptionKgs': kgs if kgs > 0 else res.production_net_weight,
                        'ContainerType': res.get_canning_move().product_id.display_name,
                        'ContainerWeightAverage': res.avg_unitary_weight,
                        'ContainerWeight': res.get_canning_move().product_id.weight,
                        'Season': res.scheduled_date.year,
                        'Tare': res.tare_weight,
                        'Warehouse': res.location_dest_id.name,
                        'QualityWeight': res.quality_weight,
                        'ContainerQuantity': res.get_canning_move().quantity_done,
                        'ArticleCode': res.get_mp_move().product_id.default_code,
                        'ArticleDescription': res.get_mp_move().product_id.display_name,
                        'OdooUpdated': res.write_date
                    })
        return data

    @http.route('/api/stock_picking', type='json', methods=['GET'], auth='token', cors='*')
    def get_stock_picking(self, lot):
        res = request.env['stock.picking'].search([('name', '=', lot)])
        if res and res.partner_id.id:
            return {
                'ProducerCode': res.partner_id.id,
                'ProducerName': res.partner_id.name,
                'VarietyName': res.get_mp_move().product_id.get_variety(),
                'LotNumber': res.name,
                'DispatchGuideNumber': res.guide_number,
                'ReceptionDate': res.scheduled_date,
                'ReceptionKgs': res.production_net_weight,
                'ContainerType': res.get_canning_move().product_id.display_name,
                'ContainerWeightAverage': res.avg_unitary_weight,
                'ContainerWeight': res.get_canning_move().product_id.weight,
                'Season': res.scheduled_date.year,
                'Tare': res.tare_weight,
                'Warehouse': res.location_dest_id.name,
                'QualityWeight': res.quality_weight,
                'ContainerQuantity': res.get_canning_move().quantity_done,
                'ArticleCode': res.get_mp_move().product_id.default_code,
                'ArticleDescription': res.get_mp_move().product_id.display_name
            }
        else:
            res = request.env['dried.unpelled.history'].search([('out_lot_id.name', '=', lot)])
            if res and res.partner_id.id:
                return {
                    'ProducerCode': res.producer_id.id,
                    'ProducerName': res.producer_id.name,
                    'VarietyName': res.in_product_variety,
                    'LotNumber': res.out_lot_id.name,
                    'DispatchGuideNumber': res.lot_guide_numbers,
                    'ReceptionDate': res.finish_date,
                    'ReceptionKgs': res.total_out_weight,
                    'ContainerType': res.canning_id.display_name,
                    'ContainerWeightAverage': res.total_out_weight / res.out_serial_count,
                    'ContainerWeight': res.canning_id.weight,
                    'Season': res.finish_date.year,
                    'Warehouse': res.picking_type_id.name,
                    'ContainerQuantity': res.out_serial_count,
                    'ArticleCode': res.out_product_id.id,
                    'ArticleDescription': res.out_product_id.name
                }
            else:
                raise werkzeug.exceptions.NotFound('lote no encontrado')

    @http.route("/api/stock_picking", type='json', methods=['PUT'], auth='token', cors='*')
    def put_lot(self, lot, data):
        stock_picking_ids = request.env['stock.picking'].search([('name', '=', lot)])

        if stock_picking_ids:
            for stock_picking in stock_picking_ids:
                stock_picking.update(data)
        return {
            'lot': lot,
            'data': data
        }

    @http.route('/api/data_by_order',type='json',methods=['POST'],auth='token',cors='*')
    def get_data_by_order(self,sale_order):
        sale_order = request.env['sale.order'].search([('name','=',sale_order)])

        data = []

        if sale_order:
            mesagge= request.env['mail.message'].sudo().search([('res_id','=',sale_order.picking_ids.mapped('id'))])
            for mes in message:
                if message.tracking_value_ids.filtered(lambda a: a.new_value_char == 'Realizado'):
                    date = message.date
                else:
                    continue
            data.append({
                'ContainerNumber':sale_order.picking_ids.mapped('container_number'),
                'DispatchDate':date,
                'ClientName':sale_order.partner_id.name,
                'ClientEmail':sale_order.partner_id.email
            })
        return data
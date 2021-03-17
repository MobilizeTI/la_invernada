from odoo import http, models
from odoo.http import request
import logging
from datetime import date, timedelta, datetime
import werkzeug
import re
import time
import pytz


class StockPickingController(http.Controller):

    @http.route('/api/stock_pickings', type='json', methods=['GET'], auth='token', cors='*')
    def get_stock_pickings(self, sinceDate=None):
        date_to_search = sinceDate or (date.today() - timedelta(days=7))
        result = request.env['stock.picking'].sudo().search([('write_date','>', date_to_search)])
        #result = request.env['stock.picking'].search([])
        data = []
        if result:
            for res in result:
                if res.partner_id.id:
                    if res.picking_type_id:
                        if res.picking_type_id.code == 'incoming':
                            if res.move_ids_without_package:
                                if res.move_ids_without_package[0].product_id.product_tmpl_id.tracking != 'lot':
                                    continue
                                kgs = 0
                                if res.production_net_weight.is_integer():
                                    kgs = int(res.production_net_weight)
                                data.append({
                                    'ProducerCode': res.partner_id.id,
                                    'ProducerName': res.partner_id.name,
                                    'VarietyName': res.move_ids_without_package[0].product_id.get_variety(),
                                    'LotNumber': res.name,
                                    'DispatchGuideNumber': res.guide_number,
                                    'ReceptionDate': self.time_to_tz_naive(res.scheduled_date, pytz.utc, pytz.timezone("America/Santiago")) or self.time_to_tz_naive(res.write_date, pytz.utc, pytz.timezone("America/Santiago")),
                                    'ReceptionKgs': kgs if kgs > 0 else res.production_net_weight,
                                    'ContainerType': res.get_canning_move().product_id.display_name,
                                    'ContainerWeightAverage': res.avg_unitary_weight,
                                    'ContainerWeight': res.get_canning_move().product_id.weight,
                                    'Season': res.scheduled_date.year,
                                    'Tare': res.tare_weight,
                                    'Warehouse': res.location_dest_id.name,
                                    'QualityWeight': res.quality_weight,
                                    'ContainerQuantity': res.get_canning_move().quantity_done,
                                    'ArticleCode': res.move_ids_without_package[0].product_id.default_code,
                                    'ArticleDescription': res.move_ids_without_package[0].product_id.display_name,
                                    'OdooUpdated': res.write_date
                                })
        return data

    @http.route('/api/stock_picking', type='json', methods=['GET'], auth='token', cors='*')
    def get_stock_picking(self, lot):
        res = request.env['stock.picking'].sudo().search([('name', '=', lot)])
        if res and res.partner_id.id:
            return {
                'ProducerCode': res.partner_id.id,
                'ProducerName': res.partner_id.name,
                'VarietyName': res.move_ids_without_package[0].product_id.get_variety(),
                'LotNumber': res.name,
                'DispatchGuideNumber': res.guide_number,
                'ReceptionDate': self.time_to_tz_naive(res.scheduled_date, pytz.utc, pytz.timezone("America/Santiago")),
                'ReceptionKgs': res.production_net_weight,
                'ContainerType': res.get_canning_move().product_id.display_name,
                'ContainerWeightAverage': res.avg_unitary_weight,
                'ContainerWeight': res.get_canning_move().product_id.weight,
                'Season': res.scheduled_date.year,
                'Tare': res.tare_weight,
                'Warehouse': res.location_dest_id.name,
                'QualityWeight': res.quality_weight,
                'ContainerQuantity': res.get_canning_move().quantity_done,
                'ArticleCode': res.move_ids_without_package[0].product_id.default_code,
                'ArticleDescription': res.move_ids_without_package[0].product_id.display_name
            }
        else:
            res = request.env['dried.unpelled.history'].sudo().search(
                [('out_lot_id.name', '=', lot)])
            if res and res.producer_id.id:
                return {
                    'ProducerCode': res.producer_id.id,
                    'ProducerName': res.producer_id.name,
                    'VarietyName': res.in_product_variety,
                    'LotNumber': res.out_lot_id.name,
                    'DispatchGuideNumber': res.lot_guide_numbers,
                    'ReceptionDate': self.time_to_tz_naive(res.finish_date, pytz.utc, pytz.timezone("America/Santiago")),
                    'ReceptionKgs': res.total_out_weight,
                    'ContainerType': res.canning_id.display_name,
                    'ContainerWeightAverage': res.total_out_weight / res.out_serial_count,
                    'ContainerWeight': res.canning_id.weight,
                    'Season': res.finish_date.year,
                    'Warehouse': res.sudo().picking_type_id.name,
                    'ContainerQuantity': res.out_serial_count,
                    'ArticleCode': res.out_product_id.default_code,
                    'ArticleDescription': res.out_product_id.name
                }
            else:
                raise werkzeug.exceptions.NotFound('lote no encontrado')

    @http.route("/api/stock_picking", type='json', methods=['PUT'], auth='token', cors='*')
    def put_lot(self, lot, data):
        stock_picking_ids = request.env['stock.picking'].sudo().search(
            [('name', '=', lot)])

        if stock_picking_ids:
            for stock_picking in stock_picking_ids:
                stock_picking.update(data)
        return {
            'lot': lot,
            'data': data
        }

    @http.route('/api/data_by_order', type='json', methods=['POST'], auth='token', cors='*')
    def get_data_by_order(self, sale_order):
        sale_order = request.env['sale.order'].sudo().search(
            [('name', '=', sale_order)])
        data = []
        if sale_order:
            date = []
            picking_data = []
            mesagge = request.env['mail.message'].sudo().search(
                [('res_id', 'in', sale_order.picking_ids.mapped('id'))])
            stock_picking = request.env['stock.picking'].search(
                [('id', 'in', mesagge.mapped('res_id'))])
            for item in stock_picking:
                if item.state == 'done':
                    picking_data.append({
                        'Picking_id': item.id,
                        'Container': item.container_number,
                    })
            for mes in mesagge:
                if mes.tracking_value_ids.filtered(lambda a: a.new_value_char == 'Realizado'):
                    for value in picking_data:
                        if mes.res_id == value['Picking_id']:
                            value.update({'Date': mes.date})
                    date.append(mes.date)
                else:
                    continue
            data.append({
                'Data': picking_data,
                'DispatchedAt': date,
                'ClientName': sale_order.partner_id.name,
                'ClientEmail': sale_order.partner_id.email
            })
        return data


    def time_to_tz_naive(self,t, tz_in, tz_out):
        return tz_in.localize(datetime.combine(datetime.today(), t.time())).astimezone(tz_out)
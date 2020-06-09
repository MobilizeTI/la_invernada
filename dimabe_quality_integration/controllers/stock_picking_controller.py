from odoo import http, models
from odoo.http import request
from datetime import date, timedelta
import werkzeug



class StockPickingController(http.Controller):

    @http.route('/api/stock_pickings', type='json', methods=['GET'], auth='token', cors='*')
    def get_stock_pickings(self, sinceDate = None):
        date_to_search = sinceDate or (date.today() - timedelta(days=1))

        result = request.env['stock.picking'].search([])
        data = []
        if result:
            for res in result:
                data.append({
                'ProducerCode': res.partner_id.id,
                'ProducerName': res.partner_id.name,
                'VarietyName': res.get_mp_move().product_id.get_variety(),
                'LotNumber': res.name,
                'DispatchGuideNumber': res.guide_number,
                'ReceptionDate': res.scheduled_date or res.write_date,
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
                'ArticleDescription': res.get_mp_move().product_id.display_name,
                'OdooUpdated': res.write_date
            })
        return data 

    @http.route('/api/stock_picking', type='json', methods=['GET'], auth='token', cors='*')
    def get_stock_picking(self, lot):
        res = request.env['stock.picking'].search([('name', '=', lot)])
        if res:
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
            if res:
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

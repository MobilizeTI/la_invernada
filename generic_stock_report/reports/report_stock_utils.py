from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF


class ReportStockUtils(models.AbstractModel):
    _name = 'report.stock.utils'
    _description = 'Utilidad para generar reporte de stock'

    @api.model
    def _sum_inputs(self, lines):
        qty = 0.0
        for line in lines:
            qty += line.get('qty_in', 0.0)
        return qty
    
    @api.model
    def _sum_outputs(self, lines):
        qty = 0.0
        for line in lines:
            qty += line.get('qty_out', 0.0)
        return qty

    @api.model
    def get_lines(self, product, location, date_from=None, date_to=None):
        move_type = {
            'incoming': 'Entrada',
            'outgoing': 'Salida',
            'internal': 'Interno',
        }
        move_model = self.env["stock.move.line"]
        location_model = self.env["stock.location"]
        util_model = self.env['odoo.utils']
        if not date_from:
            date_from = fields.Datetime.to_datetime(util_model._change_time_zone(fields.Datetime.to_datetime("1970-01-01 00:00:00")).strftime(DTF))
        if not date_to:
            date_to = fields.Datetime.to_datetime(util_model._change_time_zone(datetime.combine(datetime.now(), time.max)).strftime(DTF))
        common_domain = [
            ("product_id","=",product.id),
            ("date",">=",date_from),
            ("date","<=",date_to),
            ("state","=","done"),
        ]
        all_location_ids = location_model.search([("id","child_of",[location.id])]).ids
        # find all moves coming to location
        move_in_recs = move_model.search(common_domain + [("location_dest_id","in",all_location_ids)], order="date")
        # find all moves leaving from location
        move_out_recs = move_model.search(common_domain + [("location_id","in",all_location_ids)], order="date")
        # order moves by date
        order_moves = move_in_recs + move_out_recs
        order_moves = order_moves.sorted(key=lambda x: x.date)
        lines = []
        # add opening line of report
        start_qty_in, start_qty_out = util_model.get_stock_initial(product.id, all_location_ids, date_from)
        lines.append({
            "date": date_from,
            "src": "",
            "dest": "",
            "ref": "Balance Inicial",
            "price_unit": 0,
            "amount": 0,
            "type": "",
            "partner": "",
            "qty_in": start_qty_in,
            "qty_out": start_qty_out,
            "balance": start_qty_in-start_qty_out,
        })
        # add move lines of report
        total_qty_in = start_qty_in
        total_qty_out = start_qty_out
        picking_type = False
        for move in order_moves:
            qty_in = move in move_in_recs and move.qty_done or 0.0
            qty_out = move in move_out_recs and move.qty_done or 0.0
            price_unit = move.move_id.price_unit
            total_qty_in += qty_in
            total_qty_out += qty_out
            picking_type = move.move_id.picking_type_id
            if not picking_type:
                picking_type = move.picking_id.picking_type_id
            src_name = move.location_id.name
            if move.location_id.location_id:
                src_name = move.location_id.location_id.name + ' / ' + move.location_id.name  
            dest_name = move.location_dest_id.name
            if move.location_dest_id.location_id:
                dest_name = move.location_dest_id.location_id.name + ' / ' + move.location_dest_id.name  

            lines.append({
                "date": move.date,
                "src": src_name,
                "dest": dest_name,
                "ref": move.move_id.name,
                "price_unit": price_unit,
                "amount": price_unit * (qty_in if qty_in > 0 else qty_out),
                "prodlot": move.lot_id and move.lot_id.name or '',
                "type": picking_type and move_type.get(picking_type.code, 'Interno') or 'Interno',
                "partner": move.picking_id and move.picking_id.name or '',
                "qty_in": qty_in,
                "qty_out": qty_out,
                "balance": total_qty_in-total_qty_out,
            })
        # add closing line of report
        lines.append({
            "date": date_to,
            "src": "",
            "dest": "",
            "ref": "Cierre del Balance",
            "price_unit": 0,
            "amount": 0,
            "type": "",
            "partner": "",
            "qty_in": total_qty_in,
            "qty_out": total_qty_out,
            "balance": total_qty_in-total_qty_out,
        })
        return lines
    
    @api.model
    def GetKardexIndividualData(self):
        product_model = self.env['product.product']
        location_model = self.env['stock.location']
        context = self.env.context.copy()
        product = product_model.browse(context.get('product_id'))
        location = location_model.browse(context.get('location_id'))
        date_from = context.get('date_from', False)
        date_to = context.get('date_to', False)
        lines = self.get_lines(product, location, date_from, date_to)
        sum_inputs = self._sum_inputs(lines)
        sum_outputs = self._sum_inputs(lines)
        return {
            'product': product,
            'location': location,
            'lines': lines,
            'sum_inputs': sum_inputs,
            'sum_outputs': sum_outputs,
            'date_from': date_from,
            'date_to': date_to,
        }
        
    @api.model
    def GetKardexAllData(self):
        product_model = self.env['product.product']
        categ_model = self.env['product.category']
        picking_model = self.env['stock.picking']
        location_model = self.env['stock.location']
        lot_model = self.env['stock.production.lot']
        util_model = self.env['odoo.utils']
        context = self.env.context.copy()
        start_date = context.get('start_date', False)
        end_date = context.get('end_date', False)
        if not start_date:
            start_date = fields.Datetime.to_datetime(util_model._change_time_zone(fields.Datetime.to_datetime("1970-01-01 00:00:00")).strftime(DTF))
        if not end_date:
            end_date = fields.Datetime.to_datetime(util_model._change_time_zone(datetime.now() + relativedelta(months=+1, day=1, days=-1, hour=23, minute=59, second=59)).strftime(DTF))
        filter_type = context.get('filter_type', 'by_category')
        product_ids = context.get('product_ids', [])
        category_ids = context.get('category_ids', [])
        lot_ids = context.get('lot_ids', [])
        location_ids = context.get('location_ids', [])
        if not location_ids:
            location_ids = location_model.search([('usage','=','internal')]).ids
        if filter_type == 'by_category' and category_ids:
            product_ids = product_model.search([('categ_id','in', category_ids)]).ids
        elif filter_type == 'by_lot' and lot_ids:
            SQL = """SELECT product_id FROM stock_production_lot WHERE id IN %(lot_ids)s"""
            self.env.cr.execute(SQL, {'lot_ids': tuple(lot_ids)})
            product_ids = [x[0] for x in self.env.cr.fetchall()]
        if not product_ids:
            product_ids = product_model.search([('type','!=', 'service')]).ids
        if not product_ids:
            raise UserError("There's not any product or category selected")
        location_names = ''
        category_names = ''
        lot_names = ""
        location_aux = {}
        if category_ids:
            category_names = ", ".join([x.name for x in categ_model.browse(category_ids)])
        if lot_ids:
            lot_names = ", ".join([x.display_name for x in lot_model.browse(lot_ids)])
        if location_ids:
            location_names = []
            for location in location_model.browse(location_ids):
                location_names.append(location.display_name)
                location_aux[location.id] = location.display_name
            location_names = ", ".join(location_names)
        #Obtener todos los movimientos de stock
        query = """
            SELECT sm.product_id,
                sm.location_id,
                sm.name,
                sm.date,
                sm.picking_id,
                sm.location_dest_id,
                sm.price_unit,
                sm.product_uom,
                sm.product_qty
            FROM stock_move sm
                LEFT JOIN product_product pp ON pp.id = sm.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE date >= %(start_time)s AND date <= %(end_time)s 
                AND product_id IN %(product_ids)s
                AND (sm.location_id IN %(location_ids)s OR sm.location_dest_id IN %(location_ids)s)
                AND sm.location_id != sm.location_dest_id
                AND sm.state = 'done' AND sm.product_qty != 0 AND sm.product_qty IS NOT NULL
        """ + (" AND sm.restrict_lot_id IN %(lot_ids)s" if lot_ids else "") + \
        """
            ORDER BY date ASC
        """
        params = {
            'start_time': start_date,
            'end_time': end_date,
            'product_ids': tuple(product_ids),
            'location_ids': tuple(location_ids)
        }
        if lot_ids:
            params.update({'lot_ids': tuple(lot_ids)})
        self.env.cr.execute(query, params)
        data_aux = self.env.cr.dictfetchall()
        moves_data = {}
        for data in data_aux:
            moves_data.setdefault(data['product_id'], []).append(data)
        start_data = {}
        #Obtener los saldos iniciales de cada producto
        for product in product_model.browse(product_ids):
            for location_id in location_ids:
                start_qty_in, start_qty_out = util_model.get_stock_initial(product.id, [location_id], start_date)
                start_data.setdefault(product.id, {})
                start_data[product.id].update({location_id: {
                    'product_available': start_qty_in - start_qty_out,
                    'average_price': product.standard_price,
                    'inventory_value': product.standard_price * (start_qty_in - start_qty_out),
                    }
                })
        picking, pick_name = False, False
        product_id = False
        products_data = {}
        inventory_total = 0.0
        value_total = 0.0
        for product_id in product_ids:
            products_data[product_id] = {
                                         'location_data' : {},
                                         }
            for location_id in location_ids:
                product_available = start_data[product_id][location_id]['product_available'] or 0.0
                inventory_value = start_data[product_id][location_id]['inventory_value'] or 0.0
                average_price = start_data[product_id][location_id]['average_price']
                products_data[product_id]['location_data'][location_id] = {
                    'product_available': product_available,
                    'average_price': average_price,
                    'inventory_value': inventory_value,
                    'inv_acum': 0.0,
                    'val_acum': 0.0,
                    'inputs_acum': 0.0,
                    'outputs_acum': 0.0,
                    'lines' : [],
                }
                has_move = False
                if product_id in moves_data:
                    for move_data in moves_data[product_id]:
                        if (move_data.get('location_id') == location_id or move_data.get('location_dest_id') == location_id) \
                                and (move_data.get('location_dest_id') != move_data.get('location_id')):
                            data_dict = move_data.copy()
                            has_move = True
                            #movimiento de salida
                            qty = move_data.get('product_qty')
                            move_type = 'Ingreso'
                            if move_data.get('location_id') == location_id:
                                qty = move_data.get('product_qty') * -1
                                move_type = 'Egreso'
                                products_data[product_id]['location_data'][location_id]['outputs_acum'] += qty
                            else:
                                products_data[product_id]['location_data'][location_id]['inputs_acum'] += qty
                            product_available += qty
                            inventory_total += qty
                            price_unit = move_data.get('price_unit') or 0
                            subtotal = qty * price_unit
                            inventory_value += subtotal
                            pick_name = ''
                            if move_data.get('picking_id', False):
                                picking = picking_model.browse(move_data['picking_id'])
                                pick_name = picking.name
                                if picking.partner_id:
                                    pick_name += '/' + picking.partner_id.name
                            data_dict.update({
                                              'name': data_dict.get('name', '').replace(products_data[product_id].get('name_product', ''), ''),
                                              'picking_name': pick_name,
                                              'product_qty': qty,
                                              'type': move_type,
                                              'price_unit': price_unit,
                                              'subtotal': subtotal,
                                              'inv_acum': product_available,
                                              'val_acum': inventory_value,
                                              })
                            products_data[product_id]['location_data'][location_id]['lines'].append(data_dict)
                    value_total += inventory_value
                    products_data[product_id]['location_data'][location_id]['inv_acum'] = product_available
                    products_data[product_id]['location_data'][location_id]['val_acum'] = inventory_value
                else:
                    products_data[product_id]['location_data'][location_id]['inv_acum'] = product_available
                    products_data[product_id]['location_data'][location_id]['val_acum'] = inventory_value
                    value_total += inventory_value
                    #En caso de no encontrar ningun movimiento y la bodega no tenga stock
                if not has_move and (product_available == 0.0 and inventory_value == 0.0):
                    products_data[product_id]['location_data'].pop(location_id)
        for product_id in products_data.copy():
            if not products_data[product_id]['location_data']:
                products_data.pop(product_id)
        products = product_model.search([('id','in', tuple(products_data.keys()))], order='default_code')
        return {
                'start_time': start_date,
                'end_time': end_date,
                'filter_type': filter_type,
                'location_names': location_names,
                'categ_names': category_names,
                'lot_names': lot_names,
                'products_data': products_data,
                'location_aux' : location_aux,
                'inventory_total': inventory_total,
                'products': products,
                'value_total': value_total,
        }
        
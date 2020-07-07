from odoo import fields, models, api
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'

    variety = fields.Char(
        'Variedad',
        compute='_compute_variety',
        search='_search_variety'
    )

    type_product = fields.Char(
        'Tipo de Producto'
        , compute='_compute_type_product'
    )

    label_name = fields.Char(
        'Nombre de Etiqueta'
        , compute='_compute_label_product'
    )

    caliber = fields.Char(
        'Caliber',
        compute='_compute_caliber',
        store=True
    )

    package = fields.Char('Envase', compute='_compute_package')

    is_to_manufacturing = fields.Boolean('Es Fabricacion?', default=True, compute="compute_is_to_manufacturing")

    is_standard_weight = fields.Boolean('Es peso estandar', default=False)

    measure = fields.Char('Medida', compute='_compute_measure')

    @api.multi
    def _compute_measure(self):
        for item in self:
            for value in item.attribute_value_ids.mapped('name'):
                if "Saco 10K" == value:
                    item.measure = '10 Kilos'
                if "Saco 25K" == value:
                    item.measure = '25 Kilos'

    @api.multi
    def _compute_caliber(self):
        for item in self:
            if item.get_calibers():
                item.caliber = item.get_calibers()
            else:
                item.caliber = "S/Calibre"

    @api.multi
    def _compute_package(self):
        for item in self:
            for value in item.attribute_value_ids.mapped('name'):
                if "Saco" in value:
                    item.package = 'Sacos de '

    @api.multi
    def _compute_type_product(self):
        for item in self:
            type = []
            for value in item.attribute_value_ids:
                if value.id != item.attribute_value_ids[0].id:
                    type.append(',' + value.name)
                else:
                    type.append(value.name)
            type_string = ''.join(type)
            item.type_product = type_string

    @api.multi
    def _compute_label_product(self):
        for item in self:
            specie = item.get_variant('Especie')
            if specie == 'Nuez Con Cáscara':
                item.label_name = item.name + ' (' + item.get_calibers() + ')'
            if specie == 'Nuez Sin Cáscara':
                item.label_name = item.name + ' (' + item.get_color() + ')'

    @api.multi
    def compute_is_to_manufacturing(self):
        for item in self:
            if "Fabricar" in item.route_ids.mapped('name'):
                item.update({
                    'is_to_manufacturing': True
                })

    @api.multi
    def _compute_variety(self):
        for item in self:
            item.variety = item.get_variety()

    @api.multi
    def _search_variety(self, operator, value):
        attribute_value_ids = self.env['product.attribute.value'].search([('name', operator, value)])
        product_ids = []
        if attribute_value_ids:
            product_ids = self.env['product.product'].search([
                ('attribute_value_ids', '=', attribute_value_ids.mapped('id'))
            ]).mapped('id')

        return [('id', 'in', product_ids)]

    @api.multi
    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.remaining_value',
                 'product_tmpl_id.cost_method', 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation',
                 'product_tmpl_id.categ_id.property_valuation')
    def _compute_stock_value(self):
        StockMove = self.env['stock.move']
        models._logger.error('Paso 1: {}'.format(StockMove))
        to_date = self.env.context.get('to_date')
        models._logger.error('{}'.format(to_date))
        real_time_product_ids = [product.id for product in self if product.product_tmpl_id.valuation == 'real_time']
        models._logger.error('{}'.format(real_time_product_ids))
        if real_time_product_ids:
            self.env['account.move.line'].check_access_rights('read')
            fifo_automated_values = {}
            query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                         FROM account_move_line AS aml
                        WHERE aml.product_id IN %%s AND aml.company_id=%%s %s
                     GROUP BY aml.product_id, aml.account_id"""
            models._logger.error('{}'.format(query))
            params = (tuple(real_time_product_ids), self.env.user.company_id.id)
            models._logger.error('{}'.format(params))
            if to_date:
                query = query % ('AND aml.date <= %s',)
                params = params + (to_date,)
            else:
                query = query % ('',)
            models._logger.error('{}'.format(query))
            self.env.cr.execute(query, params=params)

            res = self.env.cr.fetchall()
            raise models.ValidationError(res)
            models._logger.error('{}'.format(res))
            for row in res:
                fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        product_values = {product.id: 0 for product in self}
        product_move_ids = {product.id: [] for product in self}

        if to_date:
            domain = [('product_id', 'in', self.ids), ('date', '<=', to_date)] + StockMove._get_all_base_domain()
            value_field_name = 'value'
        else:
            domain = [('product_id', 'in', self.ids)] + StockMove._get_all_base_domain()
            value_field_name = 'remaining_value'

        StockMove.check_access_rights('read')
        query = StockMove._where_calc(domain)
        StockMove._apply_ir_rules(query, 'read')
        from_clause, where_clause, params = query.get_sql()
        query_str = """
            SELECT stock_move.product_id, SUM(COALESCE(stock_move.{}, 0.0)), ARRAY_AGG(stock_move.id)
            FROM {}
            WHERE {}
            GROUP BY stock_move.product_id
        """.format(value_field_name, from_clause, where_clause)
        self.env.cr.execute(query_str, params)
        raise models.ValidationError(self.env.cr.fetchall())
        for product_id, value, move_ids in self.env.cr.fetchall():
            product_values[product_id] = value
            product_move_ids[product_id] = move_ids

        for product in self:
            if product.cost_method in ['standard', 'average']:
                qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
                price_used = product.standard_price
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id,
                        date=to_date,
                    )
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
                if product.id == 2729:
                    raise models.UserError(
                        'Product Qty Available : {}, Price used : {} , Product Stock Value {} , Product Qty At Date {}'.format(
                            product.qty_available, price_used, product.stock_value, product.qty_at_date))
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_value = product_values[product.id]
                        product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                        product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                            0, 0, [])
                        product.stock_value = value
                        product.qty_at_date = quantity
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
                else:
                    product.stock_value = product_values[product.id]
                    product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                            0, 0, [])
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)

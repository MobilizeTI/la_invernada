from odoo import fields, models, api


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

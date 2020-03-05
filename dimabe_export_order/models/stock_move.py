from odoo import models, fields, api



class StockMove(models.Model):
    _inherit = 'stock.move'

    reserved_amount = fields.Float(
        'total',
        compute='_compute_reserved_amount'
    )

    variety = fields.Char('Variedad', compute='_get_variant')

    brand = fields.Char('Marca', compute='_get_variant')

    type_of_package = fields.Char('Tipo de Envase', compute='_get_variant')

    specie = fields.Char('Especie', compute='_get_variant')

    caliber = fields.Char('Calibre', compute='_get_variant')

    product_name = fields.Char('Producto',compute='_get_variant')


    @api.model
    def _compute_reserved_amount(self):
        self.reserved_amount = 100

    @api.onchange('product_id')
    def _get_variant(self):
        for item in self:
            result = self.env['product.product'].search([('id', '=', item.product_id.id)])
            for product in result:
                item.product_name = product.name
                for attribute in product.attribute_value_ids:
                    if attribute.attribute_id.name == 'Variedad':
                        item.variety = attribute.name
                    if attribute.attribute_id.name == 'Marca':
                        item.brand = attribute.name
                    if attribute.attribute_id.name == 'Tipo de envase':
                        item.type_of_package = attribute.name
                    if attribute.attribute_id.name == 'Especie':
                        if attribute.name == 'NUEZ CON CASCARA':
                            item.specie = 'NCC'
                        elif attribute.name == 'NUEZ SIN CASCARA':
                            item.specie = 'NSC'
                    if attribute.attribute_id.name == 'Calibre':
                        item.caliber = attribute.name

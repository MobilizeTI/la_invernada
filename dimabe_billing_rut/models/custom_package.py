from odoo import models, fields

class CustomPackage(models.Model):
    _name = 'custom.package'
    
    package_type = fields.Many2one('custom.package.type', string="Tipo de Bulto")
    quantity = fields.Float(string="Cantidad")
    brand = fields.Char(string="Marca")
    container = fields.Char(string="Container")
    stamp = fields.Char(string="Sello")


   
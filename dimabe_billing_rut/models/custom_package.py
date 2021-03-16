from odoo import models, fields

class CustomPackage(models.Model):
    _name = 'custom.package'
    
    package_type = fields.Many2one('custom.package.type', string="Tipo de Bulto")
    
    quantity = fields.Float(string="Cantidad")
    
    brand = fields.Char(string="Marca")
    
    container = fields.Char(string="Container")
    
    stamp = fields.Char(string="Sello")

    canning_type = fields.Selection(selection=lambda self: self._compute_canning_type(), string="Tipo de Envase Interno")

    invoice_id = fields.Many2one('account.invoice', auto_join = True)


    def _compute_canning_type(self):
        for item in self:
            cannig_types = self.env['product.atribute'].mapped('value_ids').search([('name','=','Tipo de envase')])
            cannings = []
            for canning in cannig_types:
                if canning.value and canning.value not in cannings:
                    cannings.append(canning.value)
            return [('primero','segundo')]



   
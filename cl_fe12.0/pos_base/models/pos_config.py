
from odoo import models, api, fields, tools
from odoo.exceptions import UserError, ValidationError

class PosConfig(models.Model):
    _inherit = 'pos.config'

    image = fields.Binary(string='Image')
    image_url = fields.Char('URL de Imagen', compute='_compute_image_url')
    pin_pricelist = fields.Char(u'Clave para cambiar Listas de Precio', size=12)
    
    @api.constrains('pin_pricelist')
    def _check_pin(self):
        for config in self:
            if config.pin_pricelist and not config.pin_pricelist.isdigit():
                raise UserError("La clave para cambiar de tarifa debe tener solo numeros")
    
    @api.depends()
    def _compute_image_url(self):
        '''
        Crear la URL para obtener la imagen del TPV
        si el parametro use_pos_logo_brand = True y hay una URL se usara esa imagen siempre
        caso contrario, se tomara la imagen del TPV, 
        y en caso de no tener imagen, se usara la imagen de company
        si la company no tiene logo, se usara la imagen por defecto de odoo
        '''
        company = self.env.user.company_id
        pos_use_logo_brand = self.env['ir.config_parameter'].sudo().get_param('use_pos_logo_brand', default="False")
        pos_logo_brand_url = self.env['ir.config_parameter'].sudo().get_param('url_pos_logo_brand', default="")
        for pos in self:
            image_url = ""
            if pos_use_logo_brand == 'True' and pos_logo_brand_url:
                image_url = pos_logo_brand_url
            else:
                params = {}
                if pos.image:
                    params = {
                        'model_name': self._name,
                        'field_image': 'image',
                        'id': pos.id,
                    }
                elif company.logo:
                    params = {
                        'model_name': company._name,
                        'field_image': 'logo',
                        'id': company.id,
                    }
                if params:
                    image_url = "/web/image?model=%(model_name)s&field=%(field_image)s&id=%(id)s" % params
            pos.image_url = image_url

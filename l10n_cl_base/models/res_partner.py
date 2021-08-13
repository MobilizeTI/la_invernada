import re

from odoo import models, api, fields, tools


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.onchange('document_type_id')
    def onchange_document_type_retail(self):
        if self.document_type_id and self.document_type_id.sii_code == 81:
            self.company_type = 'company'
        else:
            self.company_type = 'person'
            
    @api.onchange('company_type')
    def onchange_company_type_retail(self):
        if self.company_type == 'company':
            #buscar el tipod e documento RUT
            self.document_type_id = self.env['sii.document_type'].search([('sii_code','=',81)], limit=1).id
        else:
            #buscar el tipod e documento cedula
            self.document_type_id = self.env['sii.document_type'].search([('sii_code','=',82)], limit=1).id
    
    @api.onchange('city_id')
    def _onchange_city_id(self):
        res = super(ResPartner, self)._onchange_city_id()
        if not self.city_id:
            self.country_id = False
            self.state_id = False
            self.city = ""
        return res
    
    @api.multi
    def name_get(self):
        res = []
        show_document_number = self.env.context.get('show_document_number', False)
        if not show_document_number:
            return super(ResPartner, self).name_get()
        for partner in self:
            name = u"%s" % (partner.name)
            if show_document_number and partner.document_number:
                name = u"[%s] %s" % (partner.document_number, partner.name)
            res.append((partner.id, name))
        return res
    
    @api.model
    def _format_vat_and_document_number(self, vat_number):
        document_number = (re.sub('[^1234567890Kk]', '', str(vat_number))).zfill(9).upper()
        vat = 'CL%s' % document_number
        document_number_formated = '%s.%s.%s-%s' % (document_number[0:2], document_number[2:5], document_number[5:8], document_number[-1])
        return vat, document_number_formated
        
    @api.model
    def _find_partner_for_vat_or_document_number(self, vat_number, partner_id=None, extra_domain=None):
        vat, document_number = self._format_vat_and_document_number(vat_number)
        domain = [('vat', '=', vat),  ('vat', '!=',  'CL555555555'), ('parent_id', '=', False)]
        if partner_id:
            domain.append(('id', '!=', partner_id))
        if extra_domain and isinstance(extra_domain, list):
            domain.extend(extra_domain)
        #buscar por VAT, pero si no existe, buscar por document_number
        partner_found = self.search(domain, limit=1)
        if not partner_found:
            domain = [('document_number','=', document_number)]
            if partner_id:
                domain.append(('id', '!=', partner_id))
            if extra_domain and isinstance(extra_domain, list):
                domain.extend(extra_domain)
            partner_found = self.search(domain, limit=1)
        return partner_found
    
    @api.model
    def _find_or_create_sii_document(self, company_type):
        # Buscar o crear el tipo de documento
        # si es empresa buscar codigo 81(RUT), caso contrario buscar codigo 82(Cedula)
        document_model = self.env['sii.document_type']
        document_find = document_model.browse()
        if company_type == 'person':
            document_find = document_model.search([('sii_code', '=', 82)])
            if not document_find:
                document_find = document_model.create({
                    'name': 'Cedula',
                    'code': 'RUN',
                    'sii_code': 82,
                    'active': True,
                    })
        elif company_type == 'company':
            document_find = document_model.search([('sii_code', '=', 81)])
            if not document_find:
                document_find = document_model.create({
                    'name': 'RUT',
                    'code': 'RUT',
                    'sii_code': 81,
                    'active': True,
                })
        return document_find

    @api.model
    def _find_or_create_sii_responsability(self, company_type):
        # Buscar o crear la responsabilidad
        # si es empresa buscar codigo 1(IVA afecto 1ra Categoria), caso contrario buscar codigo 0(Consumidor Final
        responsability_model = self.env['sii.responsability']
        responsability_find = responsability_model.browse()
        if company_type == 'person':
            responsability_find = responsability_model.search([('tp_sii_code', '=', 0)])
            if not responsability_find:
                responsability_find = responsability_model.create({
                    'name': 'Consumidor Final',
                    'code': 'CF',
                    'tp_sii_code': 0,
                    'active': True,
                })
        elif company_type == 'company':
            responsability_find = responsability_model.search([('tp_sii_code', '=', 1)])
            if not responsability_find:
                responsability_find = responsability_model.create({
                    'name': 'IVA Afecto / 1ra Categoría',
                    'code': 'IVARI',
                    'tp_sii_code': 1,
                    'active': True,
                })
        return responsability_find
        
    @api.model
    def _find_or_create_sii_activity_description(self, company_type):
        # Buscar o crear el giro
        GiroModel = self.env['sii.activity.description']
        giro_find = GiroModel.browse()
        if company_type == 'person':
            giro_find = GiroModel.search([('name','ilike','SIN GIRO')], limit=1)
            if not giro_find:
                giro_find = GiroModel.create({'name': 'SIN GIRO'})
        return giro_find
        

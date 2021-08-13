from odoo import api, fields, models


class AccountAnalyticDefault(models.Model):    
    _inherit = 'account.analytic.default' 

    warehouse_id = fields.Many2one('stock.warehouse', 'Tienda')

    @api.model
    def account_get(self, product_id=None, partner_id=None, user_id=None, date=None, company_id=None):
        #para no cambiar la firma de la funcion, obtener el almacen desde el contexto
        warehouse_id = self.env.context.get('warehouse_id')
        if not warehouse_id:
            return super(AccountAnalyticDefault, self).account_get(product_id=product_id, partner_id=partner_id, user_id=user_id, date=date, company_id=company_id)
        domain = []
        if warehouse_id:
            domain += ['|', ('warehouse_id', '=', warehouse_id)]
        domain += [('warehouse_id', '=', False)]
        if product_id:
            domain += ['|', ('product_id', '=', product_id)]
        domain += [('product_id', '=', False)]
        if partner_id:
            domain += ['|', ('partner_id', '=', partner_id)]
        domain += [('partner_id', '=', False)]
        if company_id:
            domain += ['|', ('company_id', '=', company_id)]
        domain += [('company_id', '=', False)]
        if user_id:
            domain += ['|', ('user_id', '=', user_id)]
        domain += [('user_id', '=', False)]
        if date:
            domain += ['|', ('date_start', '<=', date), ('date_start', '=', False)]
            domain += ['|', ('date_stop', '>=', date), ('date_stop', '=', False)]
        best_index = -1
        res = self.env['account.analytic.default']
        for rec in self.search(domain):
            index = 0
            if rec.warehouse_id: index += 1
            if rec.product_id: index += 1
            if rec.partner_id: index += 1
            if rec.company_id: index += 1
            if rec.user_id: index += 1
            if rec.date_start: index += 1
            if rec.date_stop: index += 1
            if index > best_index:
                res = rec
                best_index = index
        return res

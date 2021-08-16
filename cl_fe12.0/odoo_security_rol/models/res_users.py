from odoo import models, api, fields


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    rol_ids = fields.Many2many('res.groups.rol', 'res_groups_rol_user_rel', 'user_id', 'rol_id', 'Roles')
    
    @api.multi
    def write(self, vals):
        rol_model = self.env['res.groups.rol']
        user_data = {}
        if 'rol_ids' in vals:
            for user in self:
                user_data.setdefault(user.id, []).extend(user.rol_ids.ids)
        res = super(ResUsers, self).write(vals)
        if 'rol_ids' in vals:
            new_rol_ids = vals['rol_ids'][0][2]
            for user in self:
                group_ids = user.groups_id.ids
                #quitar los grupos de los roles que ya no existe
                for rol_after_id in user_data.get(user.id, []):
                    if rol_after_id not in new_rol_ids:
                        for group in rol_model.browse(rol_after_id).groups_ids:
                            if group.id in group_ids:
                                user.write({'groups_id': [(3, group.id)]})
                #agregar los grupos de los nuevos roles
                for rol in rol_model.browse(new_rol_ids):
                    for group in rol.groups_ids:
                        if group.id not in group_ids:
                            user.write({'groups_id': [(4, group.id)]})
        
        return res
    
    @api.model
    def create(self, vals):
        new_user = super(ResUsers, self).create(vals)
        group_ids = new_user.groups_id.ids
        #agregar los grupos de los nuevos roles
        for rol in new_user.rol_ids:
            for group in rol.groups_ids:
                if group.id not in group_ids:
                    new_user.write({'groups_id': [(4, group.id)]})
        return new_user

from odoo import models, api, fields


class ResGroupsRol(models.Model):
    _name = 'res.groups.rol'
    _description = 'Roles de Usuarios'
    
    name = fields.Char(string='Nombre', size=255, required=True)
    groups_ids = fields.Many2many('res.groups', 'res_groups_rol_group_rel', 'rol_id', 'group_id', 'Grupos')
    users_ids = fields.Many2many('res.users', 'res_groups_rol_user_rel', 'rol_id', 'user_id', 'Usuarios', copy=False)
    
    @api.multi
    def write(self, vals):
        rol_data = {}
        if 'groups_ids' in vals:
            for rol in self:
                rol_data.setdefault(rol.id, []).extend(rol.groups_ids.ids)
        res = super(ResGroupsRol, self).write(vals)
        if 'groups_ids' in vals:
            new_groups_ids = vals['groups_ids'][0][2]
            for rol in self:
                group_ids = rol.groups_ids.ids
                #quitar los grupos de los roles que ya no existe
                for group_after_id in rol_data.get(rol.id, []):
                    if group_after_id not in group_ids:
                        for user in rol.users_ids:
                            if group_after_id in user.groups_id.ids:
                                user.write({'groups_id': [(3, group_after_id)]})
                #agregar los grupos de los nuevos roles
                for group_id in new_groups_ids:
                    for user in rol.users_ids:
                        if group_id not in user.groups_id.ids:
                            user.write({'groups_id': [(4, group_id)]})
        return res

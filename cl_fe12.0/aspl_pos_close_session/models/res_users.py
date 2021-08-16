# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import fields, models, api, SUPERUSER_ID, _


class res_users(models.Model):
    _inherit = 'res.users'

    login_with_pos_screen = fields.Boolean(string="Login with Direct POS")
    default_pos = fields.Many2one('pos.config',string="POS Config")
    has_group_see_cash_values = fields.Boolean('Puede ver Valores de caja?', 
        compute='_compute_has_group_see_cash_values')
    
    @api.depends()
    def _compute_has_group_see_cash_values(self):
        for user in self:
            user.has_group_see_cash_values = user.has_group('aspl_pos_close_session.group_pos_see_cash_values')

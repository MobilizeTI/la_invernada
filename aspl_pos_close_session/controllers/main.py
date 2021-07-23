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

import odoo
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import Home, ensure_db


class Home(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        res = super(Home, self).web_login(redirect, **kw)
        if request.params['login_success'] and kw.get('login'):
            UserModel = request.env['res.users']
            users = UserModel.search(UserModel._get_login_domain(kw.get('login')), limit=1)
            if users.login_with_pos_screen:
                pos_session = request.env['pos.session'].sudo().search([
                    ('config_id', '=', users.default_pos.id), 
                    ('state', '=', 'opened'),
                ], limit=1)
                if pos_session:
                    return http.redirect_with_hash('/pos/web')
                else:
                    session_id = users.default_pos.open_session_cb()
                    pos_session = request.env['pos.session'].sudo().search([
                        ('config_id', '=', users.default_pos.id),
                        ('state', '=', 'opening_control'),
                    ], limit=1)
                    if users.default_pos.cash_control:
                        pos_session.write({'opening_balance': True})
                    session_open = pos_session.action_pos_session_open()
                    return http.redirect_with_hash('/pos/web')
            else:
                return res
        else:
            return res

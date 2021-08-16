# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import safe_eval


class BaseConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auth_admin_passkey_send_to_admin = fields.Boolean(
        'Send email to admin user.',
        config_parameter="auth_admin_passkey.send_to_admin",
        help=('When the administrator use his password to login in '
              'with a different account, Odoo will send an email '
              'to the admin user.'),
    )
    auth_admin_passkey_send_to_user = fields.Boolean(
        string='Send email to user.',
        config_parameter="auth_admin_passkey.send_to_user",
        help=('When the administrator use his password to login in '
              'with a different account, Odoo will send an email '
              'to the account user.'),
    )

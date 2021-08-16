import odoo.addons.web.controllers.main as main

from odoo import http
from odoo.http import request

class Extension(main.WebClient):
    
    @http.route()
    def translations(self, mods=None, lang=None):
        res = super(Extension, self).translations(mods, lang)
        if lang is None:
            lang = request.context["lang"]
        langs = request.env['res.lang'].sudo().search([("code", "=", lang)])
        if langs:
            lang_params = langs.read([
                "name", "direction", "year_format", "month_format", "date_format", "time_format",
                "grouping", "decimal_point", "thousands_sep", "week_start"])[0]
            res['lang_parameters'] = lang_params
        return res

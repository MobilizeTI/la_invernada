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

from odoo import api, models


class report_mass_payment(models.AbstractModel):
    _name = 'report.mass_payment.report_mass_payment_temp'
    _description = 'Reporte de pagos masivos' 

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('mass_payment.report_mass_payment_temp')
        return {
                'doc_ids': self.env['mass.payment'].browse(docids),
                'doc_model': report.model,
                'docs': self,
                'data':data
                }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
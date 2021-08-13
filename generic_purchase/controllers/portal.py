from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.purchase.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    
    @http.route(['/my/purchase/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_purchase_order(self, order_id=None, access_token=None, **kw):
        report_type = kw.get('report_type')
        download = kw.get('download')
        try:
            order_sudo = self._document_check_access('purchase.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type, report_ref='purchase.action_report_purchase_order', download=download)
        values = self._purchase_order_get_page_view_values(order_sudo, access_token, **kw)
        return request.render("generic_purchase.generic_portal_my_purchase_order", values)


from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    @api.multi
    def action_create_picking(self):
        if not self.env.context.get('create_picking_from_wizard') and self.type == 'out_invoice':
            WizardModel = self.env['wizard.create.picking.from.invoice']
            view_id_xml = 'l10n_cl_stock.wizard_create_picking_from_invoice_form_view'
            new_wizard = WizardModel.create({
                'invoice_id': self.id,
                'partner_id': self.partner_id.id,
                'use_documents': True,
            })
            res = self.env['odoo.utils'].show_view("Opciones para crear Guia", WizardModel._name, view_id_xml, new_wizard.id)
        else:
            res = super(AccountInvoice, self).action_create_picking()
        return res

    @api.multi
    def _prepare_stock_picking(self, picking_type, location_id, location_dest_id, origin, picking_date):
        vals = super(AccountInvoice, self)._prepare_stock_picking(picking_type, location_id, location_dest_id, origin, picking_date)
        vals['reference']  = [(0,0, {
            'origen': int(self.sii_document_number),
            'sii_referencia_TpoDocRef': self.document_class_id.id,
            'date': self.date_invoice,
        })]
        # actulizar la informacion adicional que se pueda pasar desde el asistente
        if self.env.context.get('picking_info_aditional'):
            vals.update(self.env.context.get('picking_info_aditional'))
        return vals


class AccountInvoiceLine(models.Model):    
    _inherit = 'account.invoice.line'

    @api.multi
    def _prepare_stock_move(self, picking, location_id, location_dest_id, origin, picking_date):
        vals_move = super(AccountInvoiceLine, self)._prepare_stock_move(picking, location_id, location_dest_id, origin, picking_date)
        vals_move.update({
            'move_line_tax_ids': [(6, 0, self.invoice_line_tax_ids.ids)],
            'discount': self.discount,
            'discount_value': self.discount_value,
            'precio_unitario':  self.price_unit,
        })
        return vals_move
        
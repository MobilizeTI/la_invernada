from datetime import datetime
from collections import OrderedDict

from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools.float_utils import float_is_zero


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    partner_ref = fields.Char('Referencia del Proveedor', readonly=True, index=True)
    print_line_number = fields.Boolean(string='Print line number', help="Print line number on Picking", default=False)
    
    @api.model
    def _get_extra_domain(self):
        user_model = self.env['res.users']
        domain = []
        picking_type_ids = []
        if not user_model.has_group('stock.group_stock_manager') \
                and not user_model.has_group('l10n_cl_stock.group_validate_guias') \
                and not self.env.context.get('show_all_location',False):
            picking_type_ids = user_model.get_all_picking_type().ids
            if picking_type_ids:
                domain.append(('picking_type_id','in', picking_type_ids))
        return domain
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        args.extend(self._get_extra_domain())
        res = super(StockPicking, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
        return res
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain.extend(self._get_extra_domain())
        res = super(StockPicking, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
    
    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        res = super(StockPicking, self).onchange_picking_type()
        move_reason = self.move_reason or '1'
        if self.partner_id and self.partner_id in self.env.user.company_id.partner_id.child_ids:
            move_reason = '5' #traslados internos
        self.move_reason = move_reason
        return res
    
    @api.multi
    def button_validate(self):
        def check_lines():
            #calcular si es necesario partir el documento xq tiene muchas lineas
            ctx = self.env.context.copy()
            ctx['active_model'] = self._name
            ctx['active_ids'] = self.ids
            wizard_model = self.env['wizard.split.document.manual'].with_context(ctx)
            for picking in self.filtered('use_documents'):
                document_number, document_lines = picking._compute_total_documents()
                if document_number > 1:
                    wizard_rec = wizard_model.create({
                        'document_number': document_number,
                        'document_lines': document_lines,
                        'model_name': self._name,
                    })
                    return wizard_rec.show_view()
        #cuando no hay back_order es xq se va a procesar todo
        #calcular si es necesario partir el documento xq tiene muchas lineas
        if not self._check_backorder():
            res = check_lines()
            if res:
                return res 
        res = super(StockPicking, self).button_validate()
        #cuando hay algo de respuesta, es xq se devuelve una accion
        #para backorder o para procesar inmediatamente
        #calcular si es necesario partir el documento xq tiene muchas lineas
        if res:
            action_wizard = check_lines()
            if action_wizard: 
                return action_wizard
        return res
    
    @api.multi
    def _get_number_lines(self):
        max_number_documents = self.env.user.company_id.max_number_documents
        if self.document_class_id.max_number_documents > 0:
            max_number_documents = self.document_class_id.max_number_documents
        return max_number_documents
    
    @api.multi
    def _get_lines_to_split(self):
        no_quantities_done = all(line.quantity_done == 0.0 for line in self.move_lines)
        #si no se ha especificado ninguna cantidad, tomar todas las lineas
        if no_quantities_done:
            move_lines = self.move_lines
        else:
            move_lines = self.move_lines.filtered(lambda x: not float_is_zero(x.quantity_done, precision_rounding=x.product_id.uom_id.rounding))
        return move_lines
    
    @api.multi
    def _compute_total_documents(self):
        #si se ha configurado algo en la tienda verificar si se excede en lineas segun dicha configuracion
        document_number = 1
        number_lines = self._get_number_lines()
        move_lines = self._get_lines_to_split()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        show_quantities_grouped = ICPSudo.get_param('show_quantities_grouped', default='show_detail')
        if show_quantities_grouped == 'show_grouped':
            remision_number_lines = len(move_lines.mapped('product_id.product_tmpl_id'))
        else:
            remision_number_lines = len(move_lines)
        if number_lines > 0 and remision_number_lines > number_lines:
            document_number = self.env['odoo.utils'].compute_total_documents(remision_number_lines, number_lines)
        return document_number, number_lines
    
    @api.multi
    def get_clear_remision_backorder_vals(self):
        """
        Devuelve los valores que deben pasar a la nueva guia cuando se hace transferencia parcial
        por lo general debo encerar todos los valores relacionados al transporte
        para que cuando realmente se vayan a despachar, se ingresen los datos
        """
        vals = {
            'sii_document_number': False,
        }
        if not self.env.context.get('cancel_backorder', False):
            vals['name'] = self.picking_type_id.sequence_id.next_by_id()
        return vals
    
    @api.model
    def split_delivery(self, remision_id):
        aditional_picking_id = False
        remision = self.browse(remision_id)
        document_number, document_lines = remision._compute_total_documents()
        new_remision = False
        if document_number > 1:
            move_with_qty_lines = remision.move_lines.filtered(lambda x: not float_is_zero(x.quantity_done, precision_rounding=x.product_id.uom_id.rounding))
            #las cantidades que no se van a procesar dejarlas en un picking independiente
            #dividir solo las lineas a procesar
            moves_remaining = remision.move_lines - move_with_qty_lines
            if moves_remaining and move_with_qty_lines:
                new_remision = remision.copy({'move_lines': []})
                vals_new = {
                    'name': remision.name,
                }
                move_with_qty_lines.write({'picking_id': new_remision.id})
                move_with_qty_lines.mapped('move_line_ids').write({'picking_id': new_remision.id})
                #al picking sin procesar generarle un nuevo secuencial
                #cuando se vaya a procesar y asignen numero de guia, tomara el nombre correcto
                vals_old = remision.get_clear_remision_backorder_vals()
                remision.write(vals_old)
                new_remision.write(vals_new)
                new_remision.action_confirm()
                aditional_picking_id = new_remision.id
                #despues de pasar las lineas a procesar a un nuevo picking, ese picking es el que se va a dividir
                remision = new_remision
            new_remision = remision.copy({
                'move_lines': [],
                'move_line_ids': [],
                'backorder_id': remision.id
            })
            move_line_recs = remision._get_lines_to_split()[document_lines:] 
            move_line_recs.write({'picking_id': new_remision.id})
            move_line_recs.mapped('move_line_ids').write({'picking_id': new_remision.id})
            new_remision.message_post(
                body='Este documento se creo desde <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> por tener muchas lineas.' % (remision.id, remision.display_name))
            new_remision.action_confirm()
        return new_remision and new_remision.id or False, aditional_picking_id
    
    @api.multi
    def check_picking_state_to_transfer(self):
        for pick in self:
            if pick.state not in ('confirmed','assigned'):
                raise UserError("No puede procesar este albaran o ya ha sido procesado, por favor refresque la pantalla y vuelva a intentarlo nuevamente")
        return True
            
    @api.multi
    def getTotalDiscount(self):
        total_discount = 0
        for l in self.move_lines:
            total_discount +=  (((l.discount or 0.00) /100) * l.precio_unitario * l.product_uom_qty)
        return self.currency_id.round(total_discount)
    
    
    def _picking_lines(self):
        line_number = 1
        picking_lines = []
        no_product = False
        MntExe = 0
        default_data = OrderedDict({
            'QtyItem': 0.0,
            'MontoItem': 0.0,
            'product': False,
            'MntExe': 0.0,
            'PrcItem': 0.0,
            'DscItem': False,
            'UnmdItem': "",
            'taxInclude': False,
            'IndExe': 0,
            'DescuentoPct': 0.0,
            'DescuentoMonto': 0.0,
        })
        product_data = OrderedDict()
        line_key = False
        for line in self.move_lines:
            line_key = (line.product_id.product_tmpl_id, line.discount)
            product_data.setdefault(line_key, default_data.copy())
            product_data[line_key]['product'] = line.product_id
            product_data[line_key]['no_product'] = False
            if line.product_id.default_code == 'NO_PRODUCT':
                product_data[line_key]['no_product'] = True
            taxInclude = False
            product_data[line_key].setdefault("Impuesto",  [])
            if line.move_line_tax_ids:
                for t in line.move_line_tax_ids:
                    if t.sii_code in [26, 27, 28, 35, 271]:#@Agregar todos los adicionales
                        product_data[line_key]['CodImpAdic'] = t.sii_code
                    taxInclude = t.price_include
                    if t.amount == 0 or t.sii_code in [0]:#@TODO mejor manera de identificar exento de afecto
                        product_data[line_key]['IndExe'] = 1
                        product_data[line_key]['MntExe'] += int(round(line.subtotal, 0))
                    else:
                        amount = t.amount
                        if t.sii_code in [28, 35]:
                            amount = t.compute_factor(line.product_uom)
                        product_data[line_key]["Impuesto"].append(
                                {
                                    "CodImp": t.sii_code,
                                    'price_include': taxInclude,
                                    'TasaImp': amount,
                                }
                        )
            product_data[line_key]['taxInclude'] = taxInclude
            product_data[line_key]['DscItem'] = self._acortar_str(line.name, 1000) #descripción más extenza
            product_data[line_key]['UnmdItem'] = line.product_uom.name[:4]
            product_qty = line.product_uom_qty
            if line.state == 'done':
                product_qty = line.quantity_done
            qty = round(product_qty, 4)
            if not product_data[line_key]['no_product']:
                product_data[line_key]['QtyItem'] += qty
            if qty == 0 and not product_data[line_key]['no_product']:
                product_data[line_key]['QtyItem'] = 1
            if not product_data[line_key]['no_product']:
                if line.precio_unitario > 0:
                    product_data[line_key]['PrcItem'] = round(line.precio_unitario, 4)
            if line.discount > 0:
                product_data[line_key]['DescuentoPct'] = line.discount
                product_data[line_key]['DescuentoMonto'] = int(round((((line.discount / 100) * product_data[line_key]['PrcItem'])* qty)))
            if not product_data[line_key]['no_product'] :
                product_data[line_key]['MontoItem'] += int(round(line.subtotal if taxInclude else line.price_untaxed, 0))
            if product_data[line_key]['no_product']:
                product_data[line_key]['MontoItem'] = 0
        for line in list(product_data.values()):
            product = line['product']
            taxInclude = line['taxInclude'] 
            if product.default_code == 'NO_PRODUCT':
                no_product = True
            lines = OrderedDict()
            lines['NroLinDet'] = line_number
            if product.default_code and not no_product:
                lines['CdgItem'] = {}
                lines['CdgItem']['TpoCodigo'] = 'INT1'
                lines['CdgItem']['VlrCodigo'] = product.default_code
            MntExe += line['MntExe']
            if line['IndExe'] == 1:
                lines['IndExe'] = 1
            lines['Impuesto'] = line.get('Impuesto', [])
            if line.get('CodImpAdic', ""):
                lines['CodImpAdic'] = line.get('CodImpAdic', "")
            lines['NmbItem'] = self._acortar_str(product.name,80) #
            lines['DscItem'] = self._acortar_str(line['DscItem'], 1000) #descripción más extenza
            if product.default_code:
                lines['NmbItem'] = self._acortar_str(product.name.replace('['+product.default_code+'] ',''),80)
            
            lines['QtyItem'] = line['QtyItem']
            if lines['QtyItem'] < 0:
                raise UserError("¡No puede ser menor o igual que 0!, tiene líneas con cantidad realizada 0")
            if self.move_reason in ['5']:
                no_product = True
            if not no_product:
                lines['UnmdItem'] = line['UnmdItem']
                lines['PrcItem'] = line['PrcItem']
            if line['DescuentoPct'] > 0:
                lines['DescuentoPct'] = line['DescuentoPct']
                lines['DescuentoMonto'] = int(line['DescuentoMonto'])
            if not no_product :
                lines['MontoItem'] = int(round(line['MontoItem'],0))
            if no_product:
                lines['MontoItem'] = 0
            line_number += 1
            picking_lines.append(lines)
            if 'IndExe' in lines:
                taxInclude = False
        if len(picking_lines) == 0:
            raise UserError(_('No se puede emitir una guía sin líneas'))
        return {
            'Detalle': picking_lines,
            'MntExe': MntExe,
            'no_product':no_product,
            'tax_include': taxInclude,
        }
        
    @api.multi
    def _prepare_invoice_vals(self, journal, invoice_type):
        invoice_vals = super(StockPicking, self)._prepare_invoice_vals(journal, invoice_type)
        if invoice_type in ('out_invoice', 'out_refund') and self.use_documents:
            reference = {
                'origen': int(self.sii_document_number),
                'sii_referencia_TpoDocRef': self.location_id.sii_document_class_id.id,
                'motivo': self.note or '',
                'fecha_documento': fields.Datetime.context_timestamp(self, self.scheduled_date).strftime(DTF)
            }
            invoice_vals['referencias'] = [(0, 0, reference)] 
        return invoice_vals
        
    @api.multi
    def _get_price_unit_for_invoice(self, invoice, move_line):
        if invoice.type in ('out_invoice', 'out_refund'):
            price_unit = move_line.product_id.uom_id._compute_price(move_line.precio_unitario, move_line.product_uom)
        else:
            price_unit = super(StockPicking, self)._get_price_unit_for_invoice(invoice, move_line)
        return price_unit
    
    @api.multi
    def _prepare_invoice_line_vals(self, invoice, move_line):
        invoice_line_vals = super(StockPicking, self)._prepare_invoice_line_vals(invoice, move_line)
        invoice_line_vals['discount'] = move_line.discount
        invoice_line_vals['invoice_line_tax_ids'] = [(6, 0, move_line.move_line_tax_ids.ids)]
        if not invoice_line_vals.get('account_analytic_id', False):
            account_analytic_model = self.env['account.analytic.account']
            warehouse = move_line.warehouse_id
            if not warehouse:
                warehouse = move_line.picking_id.picking_type_id.warehouse_id
            account_analytic_recs = False
            if warehouse:
                account_analytic_recs = account_analytic_model.search([('warehouse_id', '=', warehouse.id)], limit=1)
            if not account_analytic_recs:
                account_analytic_recs = account_analytic_model.search([], limit=1)
            if account_analytic_recs:
                invoice_line_vals['account_analytic_id'] = account_analytic_recs[0].id
        return invoice_line_vals

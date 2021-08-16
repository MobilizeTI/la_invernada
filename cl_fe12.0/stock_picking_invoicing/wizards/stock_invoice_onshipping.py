# Copyright (C) 2019-Today: Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


JOURNAL_TYPE_MAP = {
    ('outgoing', 'customer'): ['out_invoice'],
    ('outgoing', 'supplier'): ['in_refund'],
    ('outgoing', 'transit'): ['out_invoice', 'in_refund'],
    ('incoming', 'supplier'): ['in_invoice'],
    ('incoming', 'customer'): ['out_refund'],
    ('incoming', 'transit'): ['in_invoice', 'out_refund'],
}


class StockInvoiceOnshipping(models.TransientModel):
    _name = 'stock.invoice.onshipping'
    _description = "Stock Invoice Onshipping"

    @api.model
    def _get_invoice_type(self):
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            active_ids = active_ids[0]
        pick_obj = self.env['stock.picking']
        picking = pick_obj.browse(active_ids)
        if not picking or not picking.move_lines:
            return 'out_invoice'
        pick_type_code = picking.picking_type_id.code
        line = fields.first(picking.move_lines)
        if pick_type_code == 'incoming':
            usage = line.location_id.usage
        else:
            usage = line.location_dest_id.usage
        return JOURNAL_TYPE_MAP.get((pick_type_code, usage), ['out_invoice'])[0]

    invoice_type = fields.Selection(
        selection=[
            ('in_refund', 'Refund Purchase'),
            ('in_invoice', 'Create Supplier Invoice'),
            ('out_refund', 'Refund Sale'),
            ('out_invoice', 'Create Customer Invoice')
        ],
        default=_get_invoice_type,
        readonly=True,
    )
    group = fields.Selection(
        selection=[
            ('picking', 'Picking'),
            ('partner', 'Partner'),
            ('partner_product', 'Partner/Product'),
        ],
        default="picking",
        help="Group pickings/moves to create invoice(s):\n"
             "Picking: One invoice per picking;\n"
             "Partner: One invoice for each picking's partner;\n"
             "Partner/Product: One invoice per picking's partner and group "
             "product into a single invoice line.",
        required=True,
    )
    invoice_date = fields.Date()
    journal_id = fields.Many2one(string="Journal",
        comodel_name='account.journal',
        ondelete="cascade",
    )
    
    @api.onchange('invoice_type')
    def _onchange_invoice_type(self):
        domain = {}
        warning={}
        journal_type = "sale"
        if self.invoice_type in ('in_invoice', 'in_refund'):
            journal_type = 'purchase'
        domain['journal_id'] = [('type', '=', journal_type)]
        if not self.journal_id:
            self.journal_id = self._default_journal(journal_type)
        return {'domain': domain, 'warning': warning}

    @api.model
    def default_get(self, fields_list):
        """
        Inherit to add default invoice_date
        :param fields_list: list of str
        :return: dict
        """
        result = super(StockInvoiceOnshipping, self).default_get(fields_list)
        result.update({
            'invoice_date': fields.Date.context_today(self),
        })
        return result

    @api.model
    def _default_journal(self, journal_type):
        """
        Get the default journal based on the given type
        :param journal_type: str
        :return: account.journal recordset
        """
        default_journal = self.env['account.journal'].search([
            ('type', '=', journal_type),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)
        return default_journal
    
    @api.multi
    def _get_id_xml_action_for_invoice(self):
        inv_type = self.invoice_type
        if inv_type in ["out_invoice", "out_refund"]:
            action = "account.action_invoice_tree1"
        else:
            action = "account.action_vendor_bill_template"
        return action

    @api.multi
    def action_generate(self):
        """
        Launch the invoice generation
        :return:
        """
        self.ensure_one()
        invoices = self._action_generate_invoices()
        if not invoices:
            raise UserError(_('No invoice created!'))
        action = self.env.ref(self._get_id_xml_action_for_invoice())
        action_dict = action.read()[0]
        if action_dict:
            action_dict.update({
                'domain': [('id', 'in', invoices.ids)],
            })
            if len(invoices) == 1:
                form_view_id = invoices.get_formview_id()
                action_dict.update({
                    'res_id': invoices.id,
                    'views': [(form_view_id, 'form')],
                })
            try:
                ctx = eval(action_dict.get('context', {}))
                ctx['search_default_this_month'] = False
                action_dict['context'] = ctx
            except:
                pass
        return action_dict

    @api.multi
    def _load_pickings(self):
        """
        Load pickings from context
        :return: stock.picking recordset
        """
        picking_obj = self.env['stock.picking']
        active_ids = self.env.context.get('active_ids', [])
        pickings = picking_obj.browse(active_ids)
        pickings = pickings.filtered(lambda p: p.invoice_state == '2binvoiced')
        return pickings

    @api.multi
    def _get_journal(self):
        """
        Get the journal depending on the journal_type
        :return: account.journal recordset
        """
        self.ensure_one()
        return self.journal_id

    @api.model
    def _get_picking_key(self, picking):
        """
        Get the key for the given picking.
        By default, it's based on the invoice partner and the picking_type_id
        of the picking
        :param picking: stock.picking recordset
        :return: key (tuple,...)
        """
        key = picking
        if self.group in ['partner', 'partner_product']:
            key = (picking._get_partner_to_invoice(), picking.picking_type_id)
        return key

    @api.multi
    def _group_pickings(self, pickings):
        """
        Group given picking
        :param pickings:
        :return: list of stock.picking recordset
        """
        grouped_picking = {}
        pickings = pickings.filtered(lambda p: p.invoice_state == '2binvoiced')
        for picking in pickings:
            key = self._get_picking_key(picking)
            picks_grouped = grouped_picking.get(
                key, self.env['stock.picking'].browse())
            picks_grouped |= picking
            grouped_picking.update({
                key: picks_grouped,
            })
        return grouped_picking.values()

    @api.multi
    def _simulate_invoice_onchange(self, values):
        """
        Simulate onchange for invoice
        :param values: dict
        :return: dict
        """
        invoice = self.env['account.invoice'].new(values.copy())
        invoice._onchange_partner_id()
        new_values = invoice._convert_to_write(invoice._cache)
        # Ensure basic values are not updated
        values.update(new_values)
        return values

    @api.multi
    def _build_invoice_values_from_pickings(self, pickings):
        """
        Build dict to create a new invoice from given pickings
        :param pickings: stock.picking recordset
        :return: dict
        """
        picking = fields.first(pickings)
        partner_id = picking._get_partner_to_invoice()
        partner = self.env['res.partner'].browse(partner_id)
        inv_type = self.invoice_type
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable_id.id
            payment_term = partner.property_payment_term_id.id
        else:
            account_id = partner.property_account_payable_id.id
            payment_term = partner.property_supplier_payment_term_id.id
        company = self.env.user.company_id
        currency = company.currency_id
        if partner:
            code = picking.picking_type_id.code
            if partner.property_product_pricelist and code == 'outgoing':
                currency = partner.property_product_pricelist.currency_id
        journal = self._get_journal()
        invoice_obj = self.env['account.invoice']
        values = invoice_obj.default_get(invoice_obj.fields_get().keys())
        values.update({
            'origin': ", ".join(pickings.mapped("name")),
            'user_id': self.env.user.id,
            'partner_id': partner_id,
            'account_id': account_id,
            'payment_term_id': payment_term,
            'type': inv_type,
            'fiscal_position_id': partner.property_account_position_id.id,
            'company_id': company.id,
            'currency_id': currency.id,
            'journal_id': journal.id,
            'picking_ids': [(4, p.id, False) for p in pickings],
            'date_invoice': self.invoice_date,
        })
        values = self._simulate_invoice_onchange(values)
        return values

    @api.multi
    def _get_move_key(self, move):
        """
        Get the key based on the given move
        :param move: stock.move recordset
        :return: key
        """
        key = move
        if self.group == 'partner_product':
            key = move.product_id
        return key

    @api.multi
    def _group_moves(self, moves):
        """
        Possibility to group moves (to create 1 invoice line with many moves)
        :param moves: stock.move recordset
        :return: list of stock.move recordset
        """
        grouped_moves = {}
        moves = moves.filtered(lambda m: m.invoice_state == '2binvoiced')
        for move in moves:
            key = self._get_move_key(move)
            move_grouped = grouped_moves.get(
                key, self.env['stock.move'].browse())
            move_grouped |= move
            grouped_moves.update({
                key: move_grouped,
            })
        return grouped_moves.values()

    @api.multi
    def _simulate_invoice_line_onchange(self, values):
        """
        Simulate onchange for invoice line
        :param values: dict
        :return: dict
        """
        line = self.env['account.invoice.line'].new(values.copy())
        line._onchange_product_id()
        new_values = line._convert_to_write(line._cache)
        # Ensure basic values are not updated
        values.update(new_values)
        return values

    @api.multi
    def _get_invoice_line_values(self, moves, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """
        line_obj = self.env['account.invoice.line']
        name = ", ".join(moves.mapped("product_id.name"))
        move = fields.first(moves)
        product = move.product_id
        fiscal_position = invoice.fiscal_position_id
        inv_type = invoice.type
        account = line_obj.get_invoice_line_account(inv_type, product, fiscal_position, invoice.company_id)
        account = move._get_account(fiscal_position, account)
        quantity = 0
        for move in moves:
            qty = move.product_uom_qty
            loc = move.location_id
            loc_dst = move.location_dest_id
            # Better to understand with IF/ELIF than many OR
            if inv_type == 'out_invoice' and loc.usage == 'customer':
                qty *= -1
            elif inv_type == 'out_refund' and loc_dst.usage == 'customer':
                qty *= -1
            elif inv_type == 'in_invoice' and loc_dst.usage == 'supplier':
                qty *= -1
            elif inv_type == 'in_refund' and loc.usage == 'supplier':
                qty *= -1
            quantity += qty
        taxes = moves._get_taxes(fiscal_position, inv_type)
        price = moves._get_price_unit_invoice(
            inv_type, invoice.partner_id, quantity)
        values = line_obj.default_get(line_obj.fields_get().keys())
        values.update({
            'name': name,
            'account_id': account.id,
            'product_id': product.id,
            'uom_id': product.uom_id.id,
            'quantity': quantity,
            'price_unit': price,
            'invoice_line_tax_ids': [(6, 0, taxes.ids)],
            'move_line_ids': [(4, m.id, False) for m in moves],
        })
        if getattr(move, 'sale_line_id'): # el campo existe solo cuando esta instalado sale_stock
            values.update({
                'discount': move.sale_line_id.discount,
                'sale_line_ids': [(6, 0, [move.sale_line_id.id])],
            })
        values = self._simulate_invoice_line_onchange(values)
        return values

    @api.multi
    def _update_picking_invoice_status(self, pickings):
        """
        Update invoice_state on pickings
        :param pickings: stock.picking recordset
        :return: stock.picking recordset
        """
        return pickings._set_as_invoiced()

    @api.multi
    def _action_generate_invoices(self):
        """
        Action to generate invoices based on pickings
        :return: account.invoice recordset
        """
        pickings = self._load_pickings()
        company = pickings.mapped("company_id")
        if company and company != self.env.user.company_id:
            raise UserError(_("All pickings are not related to your company!"))
        pick_list = self._group_pickings(pickings)
        invoices = self.env['account.invoice'].browse()
        for pickings in pick_list:
            invoice_values = self._build_invoice_values_from_pickings(pickings)
            invoice = self.env['account.invoice'].create(invoice_values)
            moves = pickings.mapped("move_lines")
            moves_list = self._group_moves(moves)
            lines = []
            for moves in moves_list:
                line_values = self._get_invoice_line_values(moves, invoice)
                if line_values:
                    lines.append(line_values)
            if lines:
                invoice.write({
                    'invoice_line_ids': [(0, False, l) for l in lines],
                })
            invoice._onchange_invoice_line_ids()
            invoices |= invoice
        # Update the state on pickings related to new invoices only
        self._update_picking_invoice_status(invoices.mapped("picking_ids"))
        return invoices

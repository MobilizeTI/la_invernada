# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class AccountStandardLedger(models.Model):
    _name = 'account.report.template'
    _description = 'Account Standard Ledger Template'

    name = fields.Char(default='Plantilla Estándar')
    ledger_type = fields.Selection(
        [('general', 'Libro Mayor'),
         ('partner', 'Cliente'),
         ('journal', 'Diarios'),
         ('open', 'Balance Abierto'),
         ('aged', 'Saldos'),
         ('analytic', 'Analítico')],
        string='Type', default='general', required=True,
        help=' * Libro Mayor : Entradas agrupadas por cuenta\n'
        ' * Cliente : Entradas agrupadas por cliente\n'
        ' * Diarios : Entradas agrupadas por diarios, sin balance inicial\n'
        ' * Balance Abierto : Diario de Aperturq\n')
    summary = fields.Boolean('Balance General', default=False,
                             help=' * Check : genera el balance general.\n'
                             ' * Uncheck : reporte detallado.\n')
    amount_currency = fields.Boolean('Con Moneda', help='Agrega la columna moneda en el reporte si '
                                     'la moneda difiere de la divisa de la empresa.')
    reconciled = fields.Boolean(
        'Entradas Conciliadas', default=True,
        help='Sólo para entradas con cuenta débito/crédito\n'
        ' * Marque esta casilla para ver las entradas conciliadas y no conciliadas con pagos.\n'
        ' * Desmarque para ver solo las entradas no conciliadas. Solo se puede usar con el libro mayor de clientes.\n')
    partner_select_ids = fields.Many2many(
        comodel_name='res.partner', string='Partners',
        domain=['|', ('is_company', '=', True), ('parent_id', '=', False)],
        help='Si está vacío, trae todos los clientes')
    account_methode = fields.Selection([('include', 'Incluído'), ('exclude', 'Excluído')], string="Método")
    account_in_ex_clude_ids = fields.Many2many(comodel_name='account.account', string='Cuentas',
                                               help='Si está vacío, trae todas las cuentas')
    analytic_account_select_ids = fields.Many2many(comodel_name='account.analytic.account', string='Cuentas Analíticas')
    init_balance_history = fields.Boolean(
        'Saldo inicial con historial.', default=True,
        help=' * Marque esta casilla si necesita informar todo el débito y la suma del crédito antes de la fecha de inicio.\n'
        ' * Desmarque esta casilla para informar solo el saldo antes de la fecha de inicio\n')
    company_id = fields.Many2one('res.company', string='Compañía', readonly=True,
                                 default=lambda self: self.env.user.company_id)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Moneda de la Compañía", readonly=True,
                                          help='Campo de utilidad para expresar el monto de la moneda', store=True)
    journal_ids = fields.Many2many('account.journal', string='Diarios', required=True,
                                   default=lambda self: self.env['account.journal'].search(
                                       [('company_id', '=', self.env.user.company_id.id)]),
                                   help='Seleccione diario, para el libro mayor abierto debe configurar todos los diarios.')
    date_from = fields.Date(string='Fecha Inicial', help='Úselo para calcular el saldo inicial.')
    date_to = fields.Date(string='Fecha Final', help='Úselo para calcular el total emparejado con el futuro.')
    target_move = fields.Selection([('posted', 'Todas las entradas publicadas'),
                                    ('all', 'Todas las entradas'),
                                    ], string='Movimientos de destino', required=True, default='posted')
    result_selection = fields.Selection([('customer', 'Clientes'),
                                         ('supplier', 'Proveedores'),
                                         ('customer_supplier', 'Clientes y Proveedores')
                                         ], string="Tipo de Empresa", required=True, default='supplier')
    report_name = fields.Char('Nombre del Reporte')
    compact_account = fields.Boolean('Cuenta compacta', default=False)

    @api.onchange('account_in_ex_clude_ids')
    def _onchange_account_in_ex_clude_ids(self):
        if self.account_in_ex_clude_ids:
            self.account_methode = 'include'
        else:
            self.account_methode = False

    @api.onchange('ledger_type')
    def _onchange_ledger_type(self):
        if self.ledger_type in ('partner', 'journal', 'open', 'aged'):
            self.compact_account = False
        if self.ledger_type == 'aged':
            self.date_from = False
            self.reconciled = False
        if self.ledger_type not in ('partner', 'aged',):
            self.reconciled = True
            return {'domain': {'account_in_ex_clude_ids': []}}
        self.account_in_ex_clude_ids = False
        if self.result_selection == 'supplier':
            return {'domain': {'account_in_ex_clude_ids': [('type_third_parties', '=', 'supplier')]}}
        if self.result_selection == 'customer':
            return {'domain': {'account_in_ex_clude_ids': [('type_third_parties', '=', 'customer')]}}
        return {'domain': {'account_in_ex_clude_ids': [('type_third_parties', 'in', ('supplier', 'customer'))]}}

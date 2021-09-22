# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, api, _
from collections import OrderedDict
import logging
_logger = logging.getLogger('TEST PURCHASE =======')
# from datetime import datetime


class CL8ColumnsReport(models.AbstractModel):
    _name = "account.eightcolumns.report.cl"
    _inherit = "account.report"
    _description = "Chilean Accounting eight columns report"

    filter_journals = True
    filter_all_entries = False
    filter_analytic = True
    filter_multi_company = None

    @property
    def filter_date(self):
        return {'mode': 'range', 'filter': 'year', 'date_from': ''}

    def _get_report_name(self):
        return _("Balance Tributario (8 columnas)")

    def _get_columns_name(self, options):
        columns = [
            {'name': _("Cuenta")},
            {'name': _("Debe"), 'class': 'number'},
            {'name': _("Haber"), 'class': 'number'},
            {'name': _("Deudor"), 'class': 'number'},
            {'name': _("Acreedor"), 'class': 'number'},
            {'name': _("Activo"), 'class': 'number'},
            {'name': _("Pasivo"), 'class': 'number'},
            {'name': _("Perdida"), 'class': 'number'},
            {'name': _("Ganancia"), 'class': 'number'}
        ]
        return columns

    @api.model
    def _prepare_query(self, options):
        tables, where_clause, where_params = self._query_get(options)

        sql_query = """
            SELECT aa.id, aa.code, aa.name,
                   SUM(account_move_line.debit) AS debe,
                   SUM(account_move_line.credit) AS haber,
                   GREATEST(SUM(account_move_line.balance), 0) AS deudor,
                   GREATEST(SUM(-account_move_line.balance), 0) AS acreedor,
                   SUM(CASE aa.internal_group WHEN 'asset' THEN account_move_line.balance ELSE 0 END) AS activo,
                   SUM(CASE aa.internal_group WHEN 'equity' THEN -account_move_line.balance ELSE 0 END) +
                   SUM(CASE aa.internal_group WHEN 'liability' THEN -account_move_line.balance ELSE 0 END) AS pasivo,
                   SUM(CASE aa.internal_group WHEN 'expense' THEN account_move_line.balance ELSE 0 END) AS perdida,
                   SUM(CASE aa.internal_group WHEN 'income' THEN -account_move_line.balance ELSE 0 END) AS ganancia
            FROM account_account AS aa, """ + tables + """
            WHERE """ + where_clause + """
            AND aa.id = account_move_line.account_id
            GROUP BY aa.id, aa.code, aa.name
            ORDER BY aa.code            
        """
        # _logger.info('Log. --ZZ tables {}'.format(tables))
        # _logger.info('Log. --ZZ where_params {}'.format(where_params))
        # tables = ''
        # where_clause_ = where_clause.replace('("account_move_line"."move_id"="account_move_line__move_id"."id") AND ', '')
        # where_clause__ = where_clause_.replace('("account_move_line__move_id"."state" != {})'.format("'cancel'"), '')
        # sql_query = """
        #     SELECT aa.id, aa.code, aa.name,
        #            SUM(account_move_line.debit) AS debe,
        #            SUM(account_move_line.credit) AS haber,
        #            GREATEST(SUM(account_move_line.balance), 0) AS deudor,
        #            GREATEST(SUM(-account_move_line.balance), 0) AS acreedor,
        #            SUM(CASE aa.internal_group WHEN 'asset' THEN account_move_line.balance ELSE 0 END) AS activo,
        #            SUM(CASE aa.internal_group WHEN 'equity' THEN -account_move_line.balance ELSE 0 END) +
        #            SUM(CASE aa.internal_group WHEN 'liability' THEN -account_move_line.balance ELSE 0 END) AS pasivo,
        #            SUM(CASE aa.internal_group WHEN 'expense' THEN account_move_line.balance ELSE 0 END) AS perdida,
        #            SUM(CASE aa.internal_group WHEN 'income' THEN -account_move_line.balance ELSE 0 END) AS ganancia
        #     FROM account_account AS aa, "account_move_line" """ + tables + """
        #     WHERE """ + where_clause + """
        #     AND aa.id = account_move_line.account_id
        #     GROUP BY aa.id, aa.code, aa.name
        #     ORDER BY aa.code            
        # """
        # _logger.info('LOG: ....>>> sql {}'.format(sql_query))
        sql_query = """
            select aa.id, aa.code, aa.name, 
                SUM(account_move_line.debit) AS debe,
                SUM(account_move_line.credit) AS haber,
                GREATEST(SUM(account_move_line.balance), 0) AS deudor,
                GREATEST(SUM(-account_move_line.balance), 0) AS acreedor,
                SUM(CASE aa.internal_group WHEN 'asset' THEN account_move_line.balance ELSE 0 END) AS activo,
                SUM(CASE aa.internal_group WHEN 'equity' THEN -account_move_line.balance ELSE 0 END) +
                SUM(CASE aa.internal_group WHEN 'liability' THEN -account_move_line.balance ELSE 0 END) AS pasivo,
                SUM(CASE aa.internal_group WHEN 'expense' THEN account_move_line.balance ELSE 0 END) AS perdida,
                SUM(CASE aa.internal_group WHEN 'income' THEN -account_move_line.balance ELSE 0 END) AS ganancia
                from account_account as aa, account_move as account_move_line__move_id, account_move_line 
                where account_move_line.move_id = account_move_line__move_id.id 
                    and account_move_line__move_id.state != %s 
                    AND account_move_line.company_id = %s
                    and account_move_line.date <= %s
                    and account_move_line.date >= %s
                    AND aa.id = account_move_line.account_id
                    AND account_move_line__move_id.state = %s
                    AND account_move_line.company_id = %s
                group by aa.id, aa.code, aa.name
                ORDER BY aa.code
         """
        return sql_query, where_params

    @api.model
    def _get_lines(self, options, line_id=None):
        # account_ids = self.env['account.account'].sudo().search([])
        lines = []
        sql_query, parameters = self._prepare_query(options)
        # _logger.info('LOG: -->>> sql {}'.format(sql_query))
        # _logger.info('LOG: -->>> params {}'.format(parameters))
        self.env.cr.execute(sql_query, parameters)
        results = self.env.cr.dictfetchall()
        for line in results:
            _logger.info('LOG: line from result {}'.format(line))
            lines.append({
                'id': line['id'],
                'name': line['code'] + " " + line['name'],
                'level': 3,
                'unfoldable': False,
                'columns': [
                    {'name': values} for values in [
                        self.format_value(line['debe']),
                        self.format_value(line['haber']),
                        self.format_value(line['deudor']),
                        self.format_value(line['acreedor']),
                        self.format_value(line['activo']),
                        self.format_value(line['pasivo']),
                        self.format_value(line['perdida']),
                        self.format_value(line['ganancia'])
                    ]
                ],
                'caret_options': 'account.account'
            })
        if lines:
            subtotals = self._calculate_subtotals(results)
            lines.append({
                'id': 'subtotals_line',
                'class': 'total',
                'name': _("Subtotal"),
                'level': 3,
                'columns': [
                    {'name': self.format_value(subtotals[key])} for key in subtotals.keys()
                ],
                'unfoldable': False,
                'unfolded': False
            })
            exercise_result = self._calculate_exercise_result(subtotals)
            lines.append({
                'id': 'exercise_result_line',
                'class': 'total',
                'name': _("Resultado del Ejercicio"),
                'level': 3,
                'columns': [
                    {'name': values} for values in [
                        '', '', '', '', '',
                        self.format_value(exercise_result['activo']),
                        self.format_value(exercise_result['pasivo']),
                        self.format_value(exercise_result['perdida']),
                        self.format_value(exercise_result['ganancia'])
                    ]
                ],
                'unfoldable': False,
                'unfolded': False
            })
            totals = self._calculate_totals(subtotals, exercise_result)
            lines.append({
                'id': 'totals_line',
                'class': 'total',
                'name': _("Total"),
                'level': 2,
                'columns': [
                    {'name': self.format_value(totals[key])} for key in totals.keys()
                ],
                'unfoldable': False,
                'unfolded': False
            })
        return lines

    def _calculate_subtotals(self, lines):
        subtotals = OrderedDict([
            ('debe', 0), ('haber', 0),
            ('deudor', 0), ('acreedor', 0),
            ('activo', 0), ('pasivo', 0),
            ('perdida', 0), ('ganancia', 0)
        ])
        for key in subtotals.keys():
            for line in lines:
                # _logger.info('LOG: -->>> lines {}'.format(line))
                subtotals[key] += line[key]
        return subtotals

    #     subtotal_line = OrderedDict(
    # [
    #     ('debe', 10994414133.02), 
    #     ('haber', 10994414133.019999), 
    #     ('deudor', 2039458103.12), 
    #     ('acreedor', 2039458103.12), 
    #     ('activo', 233192700.75), 
    #     ('pasivo', 857581742.9), 
    #     ('perdida', 1.494.374.878,37), 
    #     ('ganancia', 869.985.836,22)])

# exercise_resullt = {'pasivo': -624.389.042,1499999, 'perdida': 624.389.042,1499999, 'ganancia': 0}


    def _calculate_exercise_result(self, subtotal_line):
        exercise_result = {'activo': 0, 'pasivo': 0, 'perdida': 0, 'ganancia': 0}
        # _logger.info('LOG: -->>> subtotal_line {}'.format(subtotal_line))
        if subtotal_line['ganancia'] >= subtotal_line['perdida']:
            exercise_result['perdida'] = subtotal_line['ganancia'] - subtotal_line['perdida']
            exercise_result['pasivo'] = exercise_result['perdida']
            # exercise_result['ganancia'] = subtotal_line['ganancia'] - subtotal_line['perdida']
            # exercise_result['pasivo'] = exercise_result['ganancia']
        else:
            exercise_result['ganancia'] = subtotal_line['perdida'] - subtotal_line['ganancia']
            exercise_result['activo'] = exercise_result['perdida']
        # _logger.info('LOG: -->> exercise resullt {}'.format(exercise_result))
        return exercise_result

    def _calculate_totals(self, subtotal_line, exercise_result_line):
        totals = OrderedDict([
            ('debe', subtotal_line['debe']), ('haber', subtotal_line['haber']),
            ('deudor', subtotal_line['deudor']), ('acreedor', subtotal_line['acreedor']),
            ('activo', subtotal_line['activo'] + exercise_result_line['activo']), ('pasivo', subtotal_line['pasivo'] + exercise_result_line['pasivo']),
            ('perdida', subtotal_line['perdida'] + exercise_result_line['perdida']), ('ganancia', subtotal_line['ganancia'] + exercise_result_line['ganancia'])
        ])
        return totals


    @api.model
    def _query_get(self, options, domain=None):
        domain = self._get_options_domain(options) + (domain or [])
        self.env['account.move.line'].check_access_rights('read')
        # _logger.info('LOG: ----ZZ domain {}'.format(domain))

        query = self.env['account.move.line']._where_calc(domain)

        # Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
        self.env['account.move.line']._apply_ir_rules(query)

        return query.get_sql()   

    @api.model
    def _get_options_domain(self, options):
        domain = [
       #     ('display_type', 'not in', ('line_section', 'line_note')),
            ('move_id.state', '!=', 'cancel'),
        ]
        if options.get('multi_company', False):
            domain += [('company_id', 'in', self.env.companies.ids)]
        else:
            domain += [('company_id', '=', self.env.user.company_id.id)]
        domain += self._get_options_journals_domain(options)
        domain += self._get_options_date_domain(options)
        domain += self._get_options_analytic_domain(options)
        domain += self._get_options_partner_domain(options)
        domain += self._get_options_all_entries_domain(options)
        return domain 
    
    @api.model
    def _get_options_journals_domain(self, options):
        # Make sure to return an empty array when nothing selected to handle archived journals.
        selected_journals = self._get_options_journals(options)
        return selected_journals and [('journal_id', 'in', [j['id'] for j in selected_journals])] or []
    
    @api.model
    def _get_options_journals(self, options):
        return [
            journal for journal in options.get('journals', []) if
            not journal['id'] in ('divider', 'group') and journal['selected']
        ]
    
    @api.model
    def _get_options_date_domain(self, options):
        def create_date_domain(options_date):
            date_field = options_date.get('date_field', 'date') #options_date.get('date_field', 'date')
            domain = [(date_field, '<=', options_date['date_to'])] #date_to
            if options_date['mode'] == 'range':
                strict_range = options_date.get('strict_range')
                if not strict_range:
                    domain += [
                        '|',
                        (date_field, '>=', options_date['date_from']),#date_from
                        # ('account_id', '=', 4065)
                    ]
                else:
                    domain += [(date_field, '>=', options_date['date'])] #date_from
            _logger.info('LOG: domain {}'.format(domain))
            return domain

        if not options.get('date'):
           return []
        _logger.info('LOG:  -->>>> range_date {}'.format(options['date']))
        return create_date_domain(options['date'])

    @api.model
    def _get_options_analytic_domain(self, options):
        domain = []
        if options.get('analytic_accounts'):
            analytic_account_ids = [int(acc) for acc in options['analytic_accounts']]
            domain.append(('analytic_account_id', 'in', analytic_account_ids))
        if options.get('analytic_tags'):
            analytic_tag_ids = [int(tag) for tag in options['analytic_tags']]
            domain.append(('analytic_tag_ids', 'in', analytic_tag_ids))
        return domain

    @api.model
    def _get_options_partner_domain(self, options):
        domain = []
        if options.get('partner_ids'):
            partner_ids = [int(partner) for partner in options['partner_ids']]
            domain.append(('partner_id', 'in', partner_ids))
        if options.get('partner_categories'):
            partner_category_ids = [int(category) for category in options['partner_categories']]
            domain.append(('partner_id.category_id', 'in', partner_category_ids))
        return domain
    
    @api.model
    def _get_options_all_entries_domain(self, options):
        if not options.get('all_entries'):
            return [('move_id.state', '=', 'posted')]
        else:
            return [('move_id.state', '!=', 'cancel')]
 


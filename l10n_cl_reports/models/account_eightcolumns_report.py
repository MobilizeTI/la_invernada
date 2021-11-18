# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, api, _, fields
from collections import OrderedDict
import logging
from odoo.tools import float_is_zero
from datetime import datetime, timedelta
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
            {'name': _("Saldo Inicial"), 'class': 'number'},
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
        #     FROM account_account AS aa, """ + tables + """
        #     WHERE """ + where_clause + """
        #     AND aa.id = account_move_line.account_id
        #     GROUP BY aa.id, aa.code, aa.name
        #     ORDER BY aa.code            
        # """
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
    
    def _do_query_group_by_account_selected_range(self, options, line_id):
        """This is a wrapper to allow Localizations to leverage on this report
        without resorting to lengthy modification"""
        return self._do_query_group_by_account(options, line_id)
    
    def _do_query(self, options, line_id, group_by_account=True, limit=False):
        if group_by_account:
            select = "SELECT \"account_move_line\".account_id"
            select += ',COALESCE(SUM(\"account_move_line\".debit-\"account_move_line\".credit), 0),SUM(\"account_move_line\".amount_currency),SUM(\"account_move_line\".debit),SUM(\"account_move_line\".credit)'
            if options.get('cash_basis'):
                select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis').replace('balance', 'balance_cash_basis')
        else:
            select = "SELECT \"account_move_line\".id"
        sql = "%s FROM %s WHERE %s%s"
        if group_by_account:
            sql +=  "GROUP BY \"account_move_line\".account_id"
        else:
            sql += " GROUP BY \"account_move_line\".id"
            sql += " ORDER BY MAX(\"account_move_line\".date),\"account_move_line\".id"
            if limit and isinstance(limit, int):
                sql += " LIMIT " + str(limit)
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self._get_with_statement(user_types)
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        line_clause = line_id and ' AND \"account_move_line\".account_id = ' + str(line_id) or ''
        query = sql % (select, tables, where_clause, line_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        return results
    
    def _do_query_group_by_account(self, options, line_id):
        results = self._do_query(options, line_id, group_by_account=True, limit=False)
        used_currency = self.env.user.company_id.currency_id
        company = self.env['res.company'].browse(self._context.get('company_id')) or self.env['res.users']._get_company()
        date = self._context.get('date_to') or fields.Date.today()
        def build_converter(currency):
            def convert(amount):
                return currency._convert(amount, used_currency, company, date)
            return convert

        compute_table = {
            a.id: build_converter(a.company_id.currency_id)
            for a in self.env['account.account'].browse([k[0] for k in results])
        }
        results = dict([(
            k[0], {
                'balance': compute_table[k[0]](k[1]) if k[0] in compute_table else k[1],
                'amount_currency': k[2],
                'debit': compute_table[k[0]](k[3]) if k[0] in compute_table else k[3],
                'credit': compute_table[k[0]](k[4]) if k[0] in compute_table else k[4],
            }
        ) for k in results])
        return results
    
    def _do_query_unaffected_earnings(self, options, line_id, company=None):
        ''' Compute the sum of ending balances for all accounts that are of a type that does not bring forward the balance in new fiscal years.
            This is needed to balance the trial balance and the general ledger reports (to have total credit = total debit)
        '''

        select = '''
        SELECT COALESCE(SUM("account_move_line".balance), 0),
               COALESCE(SUM("account_move_line".amount_currency), 0),
               COALESCE(SUM("account_move_line".debit), 0),
               COALESCE(SUM("account_move_line".credit), 0)'''
        if options.get('cash_basis'):
            select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis').replace('balance', 'balance_cash_basis')
        select += " FROM %s WHERE %s"
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self._get_with_statement(user_types)
        aml_domain = [('user_type_id.include_initial_balance', '=', False)]
        if company:
            aml_domain += [('company_id', '=', company.id)]
        tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=aml_domain)
        query = select % (tables, where_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        res = self.env.cr.fetchone()
        date = self._context.get('date_to') or fields.Date.today()
        currency_convert = lambda x: company and company.currency_id._convert(x, self.env.user.company_id.currency_id, self.env.user.company_id, date) or x
        return {'balance': currency_convert(res[0]), 'amount_currency': res[1], 'debit': currency_convert(res[2]), 'credit': currency_convert(res[3])}
    
    def _group_by_account_id(self, options, line_id):
        accounts = {}
        results = self._do_query_group_by_account_selected_range(options, line_id)
        initial_bal_date_to = fields.Date.from_string(self.env.context['date_from_aml']) + timedelta(days=-1)
        initial_bal_results = self.with_context(date_to=initial_bal_date_to.strftime('%Y-%m-%d'))._do_query_group_by_account(options, line_id)

        context = self.env.context

        last_day_previous_fy = self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(self.env.context['date_from_aml']))['date_from'] + timedelta(days=-1)
        unaffected_earnings_per_company = {}
        for cid in context.get('company_ids', []):
            company = self.env['res.company'].browse(cid)
            unaffected_earnings_per_company[company] = self.with_context(date_to=last_day_previous_fy.strftime('%Y-%m-%d'), date_from=False)._do_query_unaffected_earnings(options, line_id, company)

        unaff_earnings_treated_companies = set()
        unaffected_earnings_type = self.env.ref('account.data_unaffected_earnings')
        for account_id, result in results.items():
            account = self.env['account.account'].browse(account_id)
            accounts[account] = result
            accounts[account]['initial_bal'] = initial_bal_results.get(account.id, {'balance': 0, 'amount_currency': 0, 'debit': 0, 'credit': 0})
            if account.user_type_id == unaffected_earnings_type and account.company_id not in unaff_earnings_treated_companies:
                #add the benefit/loss of previous fiscal year to unaffected earnings accounts
                unaffected_earnings_results = unaffected_earnings_per_company[account.company_id]
                for field in ['balance', 'debit', 'credit']:
                    accounts[account]['initial_bal'][field] += unaffected_earnings_results[field]
                    accounts[account][field] += unaffected_earnings_results[field]
                unaff_earnings_treated_companies.add(account.company_id)
            #use query_get + with statement instead of a search in order to work in cash basis too
            aml_ctx = {}
            if context.get('date_from_aml'):
                aml_ctx = {
                    'strict_range': True,
                    'date_from': context['date_from_aml'],
                }
            aml_ids = self.with_context(**aml_ctx)._do_query(options, account_id, group_by_account=False)
            aml_ids = [x[0] for x in aml_ids]

            accounts[account]['total_lines'] = len(aml_ids)
            offset = int(options.get('lines_offset', 0))
            if self.MAX_LINES:
                stop = offset + self.MAX_LINES
            else:
                stop = None
            if not context.get('print_mode'):
                aml_ids = aml_ids[offset:stop]

            accounts[account]['lines'] = self.env['account.move.line'].browse(aml_ids)

        # For each company, if the unaffected earnings account wasn't in the selection yet: add it manually
        user_currency = self.env.user.company_id.currency_id
        for cid in context.get('company_ids', []):
            company = self.env['res.company'].browse(cid)
            if company not in unaff_earnings_treated_companies and not float_is_zero(unaffected_earnings_per_company[company]['balance'], precision_digits=user_currency.decimal_places):
                unaffected_earnings_account = self.env['account.account'].search([
                    ('user_type_id', '=', unaffected_earnings_type.id), ('company_id', '=', company.id)
                ], limit=1)
                if unaffected_earnings_account and (not line_id or unaffected_earnings_account.id == line_id):
                    accounts[unaffected_earnings_account[0]] = unaffected_earnings_per_company[company]
                    accounts[unaffected_earnings_account[0]]['initial_bal'] = unaffected_earnings_per_company[company]
                    accounts[unaffected_earnings_account[0]]['lines'] = []
                    accounts[unaffected_earnings_account[0]]['total_lines'] = 0
        return accounts
    
    def _get_with_statement(self, user_types, domain=None):
        """ This function allow to define a WITH statement as prologue to the usual queries returned by query_get().
            It is useful if you need to shadow a table entirely and let the query_get work normally although you're
            fetching rows from your temporary table (built in the WITH statement) instead of the regular tables.

            @returns: the WITH statement to prepend to the sql query and the parameters used in that WITH statement
            @rtype: tuple(char, list)
        """
        sql = ''
        params = []

        #Cash basis option
        #-----------------
        #In cash basis, we need to show amount on income/expense accounts, but only when they're paid AND under the payment date in the reporting, so
        #we have to make a complex query to join aml from the invoice (for the account), aml from the payments (for the date) and partial reconciliation
        #(for the reconciled amount).
        if self.env.context.get('cash_basis'):
            if not user_types:
                return sql, params
            #we use query_get() to filter out unrelevant journal items to have a shadowed table as small as possible
            tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=domain)
            sql = """WITH account_move_line AS (
              SELECT \"account_move_line\".id, \"account_move_line\".date, \"account_move_line\".name, \"account_move_line\".debit_cash_basis, \"account_move_line\".credit_cash_basis, \"account_move_line\".move_id, \"account_move_line\".account_id, \"account_move_line\".journal_id, \"account_move_line\".balance_cash_basis, \"account_move_line\".amount_residual, \"account_move_line\".partner_id, \"account_move_line\".reconciled, \"account_move_line\".company_id, \"account_move_line\".company_currency_id, \"account_move_line\".amount_currency, \"account_move_line\".balance, \"account_move_line\".user_type_id, \"account_move_line\".analytic_account_id
               FROM """ + tables + """
               WHERE (\"account_move_line\".journal_id IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                 OR \"account_move_line\".move_id NOT IN (SELECT DISTINCT move_id FROM account_move_line WHERE user_type_id IN %s))
                 AND """ + where_clause + """
              UNION ALL
              (
               WITH payment_table AS (
                 SELECT aml.move_id, \"account_move_line\".date,
                        CASE WHEN (aml.balance = 0 OR sub_aml.total_per_account = 0)
                            THEN 0
                            ELSE part.amount / ABS(sub_aml.total_per_account)
                        END as matched_percentage
                   FROM account_partial_reconcile part
                   LEFT JOIN account_move_line aml ON aml.id = part.debit_move_id
                   LEFT JOIN (SELECT move_id, account_id, ABS(SUM(balance)) AS total_per_account
                                FROM account_move_line
                                GROUP BY move_id, account_id) sub_aml
                            ON (aml.account_id = sub_aml.account_id AND sub_aml.move_id=aml.move_id)
                   LEFT JOIN account_move am ON aml.move_id = am.id,""" + tables + """
                   WHERE part.credit_move_id = "account_move_line".id
                    AND "account_move_line".user_type_id IN %s
                    AND """ + where_clause + """
                 UNION ALL
                 SELECT aml.move_id, \"account_move_line\".date,
                        CASE WHEN (aml.balance = 0 OR sub_aml.total_per_account = 0)
                            THEN 0
                            ELSE part.amount / ABS(sub_aml.total_per_account)
                        END as matched_percentage
                   FROM account_partial_reconcile part
                   LEFT JOIN account_move_line aml ON aml.id = part.credit_move_id
                   LEFT JOIN (SELECT move_id, account_id, ABS(SUM(balance)) AS total_per_account
                                FROM account_move_line
                                GROUP BY move_id, account_id) sub_aml
                            ON (aml.account_id = sub_aml.account_id AND sub_aml.move_id=aml.move_id)
                   LEFT JOIN account_move am ON aml.move_id = am.id,""" + tables + """
                   WHERE part.debit_move_id = "account_move_line".id
                    AND "account_move_line".user_type_id IN %s
                    AND """ + where_clause + """
               )
               SELECT aml.id, ref.date, aml.name,
                 CASE WHEN aml.debit > 0 THEN ref.matched_percentage * aml.debit ELSE 0 END AS debit_cash_basis,
                 CASE WHEN aml.credit > 0 THEN ref.matched_percentage * aml.credit ELSE 0 END AS credit_cash_basis,
                 aml.move_id, aml.account_id, aml.journal_id,
                 ref.matched_percentage * aml.balance AS balance_cash_basis,
                 aml.amount_residual, aml.partner_id, aml.reconciled, aml.company_id, aml.company_currency_id, aml.amount_currency, aml.balance, aml.user_type_id, aml.analytic_account_id
                FROM account_move_line aml
                RIGHT JOIN payment_table ref ON aml.move_id = ref.move_id
                WHERE journal_id NOT IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                  AND aml.move_id IN (SELECT DISTINCT move_id FROM account_move_line WHERE user_type_id IN %s)
              )
            ) """
            params = [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)]
        return sql, params
    

    @api.model
    def _get_lines(self, options, line_id=None):
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        grouped_accounts = {}
        initial_balances = {}
        comparison_table = [options.get('date')]
        comparison_table += options.get('comparison') and options['comparison'].get('periods') or []

        #get the balance of accounts for each period
        period_number = 0
        for period in reversed(comparison_table):
            res = self.with_context(date_from_aml=period['date_from'], date_to=period['date_to'], date_from=period['date_from'] and company_id.compute_fiscalyear_dates(fields.Date.from_string(period['date_from']))['date_from'] or None)._group_by_account_id(options, line_id)  # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to either the beginning of the fy or the beginning of times depending on the account
            if period_number == 0:
                initial_balances = dict([(k, res[k]['initial_bal']['balance']) for k in res])
            # for account in res:
            #     if account not in grouped_accounts:
            #         grouped_accounts[account] = [{'balance': 0, 'debit': 0, 'credit': 0} for p in comparison_table]
            #     grouped_accounts[account][period_number]['balance'] = res[account]['balance'] - res[account]['initial_bal']['balance']
            #     grouped_accounts[account][period_number]['debit'] = res[account]['debit'] - res[account]['initial_bal']['debit']
            #     grouped_accounts[account][period_number]['credit'] = res[account]['credit'] - res[account]['initial_bal']['credit']
            period_number += 1
        
        
        
        

        lines = []
        sql_query, parameters = self._prepare_query(options)
        self.env.cr.execute(sql_query, parameters)
        results = self.env.cr.dictfetchall()
        ids = []
        for line in results:
            account_obj = self.env['account.account'].browse(line['id'])
            ids.append(account_obj)
        
        missing_accounts = []
        
        for key, value in initial_balances.items():
            if key not in ids:
                if value != 0:
                    missing_accounts.append({
                        key: value
                    })
                    results.append({
                        'acreedor': 0.0,
                        'activo': 0.0,
                        'code': key.code,
                        'debe': 0.0,
                        'deudor': 0.0,
                        'ganancia': 0.0,
                        'haber': 0.0,
                        'id': key.id,
                        'name': key.name,
                        'pasivo': 0.0,
                        'perdida': 0.0,
                        'initial_balance': value

                    })


        # results.sort(lambda x: x.get('code'), reverse=False)
        results = sorted(results, key=lambda x: x.get('code'), reverse=False)
        for line in results:
            account_obj = self.env['account.account'].browse(line['id'])
            if account_obj in initial_balances:
                init_account_balance = initial_balances[account_obj]
            line['balance_inicial'] = init_account_balance
            account_type = account_obj.internal_group
            if account_type == 'expense' or account_type == 'asset':
                if init_account_balance < 0:
                    line['haber'] = line['haber'] + abs(init_account_balance)
                else:
                    line['debe'] = line['debe'] + abs(init_account_balance)
            if account_type == 'liability' or account_type == 'income':
                if init_account_balance < 0:
                    line['debe'] = line['debe'] + abs(init_account_balance)
                else:
                    line['haber'] = line['haber'] + abs(init_account_balance)
            diff = line['haber'] - line['debe']
            if diff > 0:
                line['acreedor'] = abs(diff)
                line['deudor'] = 0
            else:
                line['deudor'] = abs(diff)
                line['acreedor'] = 0
            
            diff_a_d = line['acreedor'] - line['deudor']
            if account_type == 'liability' or account_type == 'asset':
                if diff_a_d > 0:
                    line['pasivo'] = abs(diff)
                    line['activo'] = 0
                else:
                    line['activo'] = abs(diff)
                    line['pasivo'] = 0
            else:
                line['activo'] = 0
                line['pasivo'] = 0
            if account_type == 'income' or account_type == 'expense':
                if diff_a_d > 0:
                    line['ganancia'] = abs(diff)
                    line['perdida'] = 0
                else:
                    line['perdida'] = abs(diff)
                    line['ganancia'] = 0
            else:
                line['perdida'] = 0
                line['ganancia'] = 0

            lines.append({
                'id': line['id'],
                'name': line['code'] + " " + line['name'],
                'level': 3,
                'unfoldable': False,
                'columns': [
                    {'name': values} for values in [
                        self.format_value(init_account_balance),
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
                        '', '', '', '',
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
            ('balance_inicial', 0),
            ('debe', 0), ('haber', 0),
            ('deudor', 0), ('acreedor', 0),
            ('activo', 0), ('pasivo', 0),
            ('perdida', 0), ('ganancia', 0)
        ])
        for key in subtotals.keys():
            for line in lines:
                subtotals[key] += line[key]
        return subtotals
    def _calculate_exercise_result(self, subtotal_line):
        exercise_result = {'activo': 0, 'pasivo': 0, 'perdida': 0, 'ganancia': 0}
        if subtotal_line['ganancia'] >= subtotal_line['perdida']:
            exercise_result['perdida'] = subtotal_line['ganancia'] - subtotal_line['perdida']
            exercise_result['pasivo'] = exercise_result['perdida']
        else:
            exercise_result['ganancia'] = subtotal_line['perdida'] - subtotal_line['ganancia']
            exercise_result['activo'] = exercise_result['ganancia']
        return exercise_result

    def _calculate_totals(self, subtotal_line, exercise_result_line):
        totals = OrderedDict([
            ('balance_inicial', subtotal_line['balance_inicial']),
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

        query = self.env['account.move.line']._where_calc(domain)
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
            # _logger.info('LOG: domain {}'.format(domain))
            return domain

        if not options.get('date'):
           return []
        # _logger.info('LOG:  -->>>> range_date {}'.format(options['date']))
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
 


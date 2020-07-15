from odoo import models, fields, api


class ReportAccountFinancialReport(models.Model):
    _inherit = 'account.financial.html.report'

    def _get_column_name(self, field_content, field):
        raise models.ValidationError("Hola")
        comodel_name = self.env['account.move.line']._fields[field].comodel_name
        if not comodel_name:
            return field_content
        grouping_record = self.env[comodel_name].browse(field_content)
        return grouping_record.name_get()[0][1] if grouping_record and grouping_record.exists() else ('Undefined')

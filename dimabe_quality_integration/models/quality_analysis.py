from odoo import fields, models, api


class QualityAnalysis(models.Model):
    _name = 'quality.analysis'
    _description = """
        clase que almacena los datos de calidad del sistema dimabe
    """

    stock_production_lot_ids = fields.One2many(
        'stock.production.lot',
        'quality_analysis_id',
        string='Lote'
    )

    lot_balance = fields.Float(
        'Stock Disponible',
        related='stock_production_lot_ids.balance',
        store=True
    )

    lot_name = fields.Char(
        compute='_compute_lot_name'
    )

    name = fields.Char('Informe')

    pre_caliber = fields.Float('Precalibre')

    caliber_ids = fields.One2many(
        'caliber.analysis',
        'quality_analysis_id',
        'Análisis Calibre'
    )

    caliber_1 = fields.Float(
        '26-28',
        compute='_compute_caliber_1'
    )
    caliber_2 = fields.Float(
        '28-30',
        compute='_compute_caliber_2'
    )
    caliber_3 = fields.Float(
        '30-32',
        compute='_compute_caliber_3'
    )
    caliber_4 = fields.Float(
        '32-34',
        compute='_compute_caliber_4'
    )
    caliber_5 = fields.Float(
        '34-36',
        compute='_compute_caliber_5'
    )
    caliber_6 = fields.Float(
        '36+',
        compute='_compute_caliber_6'
    )

    @api.model
    def get_caliber(self, name):
        return self.caliber_ids.filtered(lambda a: a.name == name)

    @api.multi
    def _compute_caliber_1(self):
        for item in self:
            item.caliber_1 = item.get_caliber('26 (mm) - 28 (mm)').percent

    @api.multi
    def _compute_caliber_2(self):
        for item in self:
            item.caliber_2 = item.get_caliber('28 (mm) - 30 (mm)').percent

    @api.multi
    def _compute_caliber_3(self):
        for item in self:
            item.caliber_3 = item.get_caliber('30 (mm) - 32 (mm)').percent

    @api.multi
    def _compute_caliber_4(self):
        for item in self:
            item.caliber_4 = item.get_caliber('32 (mm) - 34 (mm)').percent

    @api.multi
    def _compute_caliber_5(self):
        for item in self:
            item.caliber_5 = item.get_caliber('34 (mm) - 36 (mm)').percent

    @api.multi
    def _compute_caliber_6(self):
        for item in self:
            item.caliber_6 = item.get_caliber('> 36 (mm)').percent

    external_damage_analysis_ids = fields.One2many(
        'external.damage.analysis',
        'quality_analysis_id',
        'Análisis Daños Externos'
    )

    external_damage_analysis_1 = fields.Float(
        'MANCHA GRAVE',
        compute='_compute_external_damage_analysis_1'
    )

    external_damage_analysis_2 = fields.Float(
        'MEZCLA VARIEDAD',
        compute='_compute_external_damage_analysis_2'
    )

    external_damage_analysis_3 = fields.Float(
        'CASCO ABIERTO',
        compute='_compute_external_damage_analysis_3'
    )

    external_damage_analysis_4 = fields.Float(
        'CÁSCARA IMPERFECTA',
        compute='_compute_external_damage_analysis_4'
    )

    external_damage_analysis_5 = fields.Float(
        'NUEZ PARTIDA',
        compute='_compute_external_damage_analysis_5'
    )

    external_damage_analysis_6 = fields.Float(
        'NUEZ TRIZADA',
        compute='_compute_external_damage_analysis_6'
    )

    external_damage_analysis_7 = fields.Float(
        'PELÓN ADERIDO',
        compute='_compute_external_damage_analysis_7'
    )

    external_damage_analysis_8 = fields.Float(
        'HONGO ACTIVO NCC',
        compute='_compute_external_damage_analysis_8'
    )

    external_damage_analysis_9 = fields.Float(
        'HONGO INACTIVO NCC',
        compute='_compute_external_damage_analysis_9'
    )

    external_damage_analysis_10 = fields.Float(
        'MANCHA LEVE',
        compute='_compute_external_damage_analysis_10'
    )

    external_damage_analysis_11 = fields.Float(
        'TIERRA',
        compute='_compute_external_damage_analysis_11'
    )

    @api.model
    def get_external_damage(self, name):
        return self.external_damage_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    def _compute_external_damage_analysis_1(self):
        for item in self:
            item.external_damage_analysis_1 = item.get_external_damage('MANCHA GRAVE').percent

    @api.multi
    def _compute_external_damage_analysis_2(self):
        for item in self:
            item.external_damage_analysis_2 = item.get_external_damage('MEZCLA VARIEDAD').percent

    @api.multi
    def _compute_external_damage_analysis_3(self):
        for item in self:
            item.external_damage_analysis_3 = item.get_external_damage('CASCO ABIERTO').percent

    @api.multi
    def _compute_external_damage_analysis_4(self):
        for item in self:
            item.external_damage_analysis_4 = item.get_external_damage('CÁSCARA IMPERFECTA').percent

    @api.multi
    def _compute_external_damage_analysis_5(self):
        for item in self:
            item.external_damage_analysis_5 = item.get_external_damage('NUEZ PARTIDA').percent

    @api.multi
    def _compute_external_damage_analysis_6(self):
        for item in self:
            item.external_damage_analysis_6 = item.get_external_damage('NUEZ TRIZADA').percent

    @api.multi
    def _compute_external_damage_analysis_7(self):
        for item in self:
            item.external_damage_analysis_7 = item.get_external_damage('PELÓN ADERIDO').percent

    @api.multi
    def _compute_external_damage_analysis_8(self):
        for item in self:
            item.external_damage_analysis_8 = item.get_external_damage('HONGO ACTIVO NCC').percent

    @api.multi
    def _compute_external_damage_analysis_9(self):
        for item in self:
            item.external_damage_analysis_9 = item.get_external_damage('HONGO INACTIVO NCC').percent

    @api.multi
    def _compute_external_damage_analysis_10(self):
        for item in self:
            item.external_damage_analysis_10 = item.get_external_damage('MANCHA LEVE').percent

    @api.multi
    def _compute_external_damage_analysis_11(self):
        for item in self:
            item.external_damage_analysis_11 = item.get_external_damage('TIERRA').percent

    internal_damage_analysis_ids = fields.One2many(
        'internal.damage.analysis',
        'quality_analysis_id',
        'Análisis Daños Internos'
    )

    internal_damage_analysis_1 = fields.Float(
        'RESECA GRAVE',
        compute='_compute_internal_damage_analysis_1'
    )

    internal_damage_analysis_2 = fields.Float(
        'DAÑO INSECTO',
        compute='_compute_internal_damage_analysis_2'
    )

    internal_damage_analysis_3 = fields.Float(
        'RESECA LEVE',
        compute='_compute_internal_damage_analysis_3'
    )

    internal_damage_analysis_4 = fields.Float(
        'HONGO ACTIVO NSC',
        compute='_compute_internal_damage_analysis_4'
    )

    internal_damage_analysis_5 = fields.Float(
        'HONGO INACTIVO NSC',
        compute='_compute_internal_damage_analysis_5'
    )

    internal_damage_analysis_6 = fields.Float(
        'PULPA NARANJA',
        compute='_compute_internal_damage_analysis_6'
    )

    internal_damage_analysis_7 = fields.Float(
        'RANCIDEZ',
        compute='_compute_internal_damage_analysis_7'
    )

    @api.model
    def get_internal_damage(self, name):
        return self.internal_damage_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    def _compute_internal_damage_analysis_1(self):
        for item in self:
            item.internal_damage_analysis_1 = item.get_internal_damage('RESECA GRAVE').percent

    @api.multi
    def _compute_internal_damage_analysis_2(self):
        for item in self:
            item.internal_damage_analysis_2 = item.get_internal_damage('DAÑO INSECTO').percent

    @api.multi
    def _compute_internal_damage_analysis_3(self):
        for item in self:
            item.internal_damage_analysis_3 = item.get_internal_damage('RESECA LEVE').percent

    @api.multi
    def _compute_internal_damage_analysis_4(self):
        for item in self:
            item.internal_damage_analysis_4 = item.get_internal_damage('HONGO ACTIVO NSC').percent

    @api.multi
    def _compute_internal_damage_analysis_5(self):
        for item in self:
            item.internal_damage_analysis_5 = item.get_internal_damage('HONGO INACTIVO NSC').percent

    @api.multi
    def _compute_internal_damage_analysis_6(self):
        for item in self:
            item.internal_damage_analysis_6 = item.get_internal_damage('PULPA NARANJA').percent

    @api.multi
    def _compute_internal_damage_analysis_7(self):
        for item in self:
            item.internal_damage_analysis_7 = item.get_internal_damage('RANCIDEZ').percent

    humidity_analysis_id = fields.Many2one('humidity.analysis', 'Análisis de Humedad')

    humidity_percent = fields.Float(
        related='humidity_analysis_id.percent',
        string='% Humedad'

    )

    humidity_tolerance = fields.Float(
        related='humidity_analysis_id.tolerance'
    )

    performance_analysis_ids = fields.One2many(
        'performance.analysis',
        'quality_analysis_id',
        'Análisis Rendimiento'
    )

    performance_analysis_1 = fields.Float(
        'Rendimiento Partido Total',
        compute='_compute_performance_analysis_1'
    )

    performance_analysis_2 = fields.Float(
        'Rendimiento Partido Exportable',
        compute='_compute_performance_analysis_2'
    )

    @api.model
    def get_performance(self, name):
        return self.performance_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    def _compute_performance_analysis_1(self):
        for item in self:
            item.performance_analysis_1 = item.get_performance('Rendimiento Partido Total').percent

    @api.multi
    def _compute_performance_analysis_2(self):
        for item in self:
            item.performance_analysis_2 = item.get_performance('Rendimiento Partido Exportable').percent

    color_analysis_ids = fields.One2many(
        'color.analysis',
        'quality_analysis_id',
        'Análisis Color'
    )

    color_analysis_1 = fields.Float(
        'EXTRA LIGHT',
        compute='_compute_color_analysis_1'
    )

    color_analysis_2 = fields.Float(
        'EXTRA LIGHT FANCY',
        compute='_compute_color_analysis_2'
    )

    color_analysis_3 = fields.Float(
        'EXTRA LIGHT STANDAR',
        compute='_compute_color_analysis_3'
    )

    color_analysis_4 = fields.Float(
        'LIGHT',
        compute='_compute_color_analysis_4'
    )

    color_analysis_5 = fields.Float(
        'LIGHT AMBER',
        compute='_compute_color_analysis_5'
    )

    color_analysis_6 = fields.Float(
        'AMBER',
        compute='_compute_color_analysis_6'
    )

    color_analysis_7 = fields.Float(
        'AMARILLA',
        compute='_compute_color_analysis_7'
    )

    @api.model
    def get_color(self, name):
        return self.color_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    def _compute_color_analysis_1(self):
        for item in self:
            item.color_analysis_1 = item.get_color('EXTRA LIGHT').percent

    @api.multi
    def _compute_color_analysis_2(self):
        for item in self:
            item.color_analysis_2 = item.get_color('EXTRA LIGHT FANCY').percent

    @api.multi
    def _compute_color_analysis_3(self):
        for item in self:
            item.color_analysis_3 = item.get_color('EXTRA LIGHT STANDAR').percent

    @api.multi
    def _compute_color_analysis_4(self):
        for item in self:
            item.color_analysis_4 = item.get_color('LIGHT').percent

    @api.multi
    def _compute_color_analysis_5(self):
        for item in self:
            item.color_analysis_5 = item.get_color('LIGHT AMBER').percent

    @api.multi
    def _compute_color_analysis_6(self):
        for item in self:
            item.color_analysis_6 = item.get_color('AMBER').percent

    @api.multi
    def _compute_color_analysis_7(self):
        for item in self:
            item.color_analysis_7 = item.get_color('AMARILLA').percent

    form_analysis_ids = fields.One2many(
        'form.analysis',
        'quality_analysis_id',
        'Análisis Forma'
    )

    form_analysis_1 = fields.Float(
        'HALVES 7/8',
        compute='_compute_form_analysis_1'
    )

    form_analysis_2 = fields.Float(
        'QUARTERS',
        compute='_compute_form_analysis_2'
    )

    form_analysis_3 = fields.Float(
        'PIECES',
        compute='_compute_form_analysis_3'
    )

    form_analysis_4 = fields.Float(
        'HALVES 3/4',
        compute='_compute_form_analysis_4'
    )

    @api.model
    def get_form(self, name):
        return self.form_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    def _compute_form_analysis_1(self):
        for item in self:
            item.form_analysis_1 = item.get_form('HALVES 7/8').percent

    @api.multi
    def _compute_form_analysis_2(self):
        for item in self:
            item.form_analysis_2 = item.get_form('QUARTERS').percent

    @api.multi
    def _compute_form_analysis_3(self):
        for item in self:
            item.form_analysis_3 = item.get_form('PIECES').percent

    @api.multi
    def _compute_form_analysis_4(self):
        for item in self:
            item.form_analysis_4 = item.get_form('HALVES 3/4').percent

    impurity_analysis_ids = fields.One2many(
        'impurity.analysis',
        'quality_analysis_id',
        'Análisis Impureza'
    )

    impurity_analysis_1 = fields.Float(
        'SHELL',
        compute='_compute_impurity_analysis_1'
    )

    impurity_analysis_2 = fields.Float(
        'SEPTUM',
        compute='_compute_impurity_analysis_2'
    )

    impurity_analysis_3 = fields.Float(
        'FOREIGN MATERIAL',
        compute='_compute_impurity_analysis_3'
    )

    @api.model
    def get_impurity(self, name):
        return self.impurity_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    def _compute_impurity_analysis_1(self):
        for item in self:
            item.impurity_analysis_1 = item.get_impurity('SHELL').percent

    @api.multi
    def _compute_impurity_analysis_2(self):
        for item in self:
            item.impurity_analysis_2 = item.get_impurity('SEPTUM').percent

    @api.multi
    def _compute_impurity_analysis_3(self):
        for item in self:
            item.impurity_analysis_3 = item.get_impurity('FOREIGN MATERIAL').percent

    analysis_observations = fields.Text('Observaciones')

    category = fields.Char('Categoría')

    @api.model
    def create(self, values_list):
        res = super(QualityAnalysis, self).create(values_list)
        res.name = 'Informe QA {}'.format(fields.datetime.utcnow())
        return res

    @api.multi
    @api.depends('stock_production_lot_ids')
    def _compute_lot_name(self):
        for item in self:
            if item.stock_production_lot_ids and len(item.stock_production_lot_ids) > 0:
                item.lot_name = item.stock_production_lot_ids[0].name


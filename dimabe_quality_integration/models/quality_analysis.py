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
        compute='_compute_lot_name',
        string='Lote'
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
        compute='_compute_caliber_1',
        store=True
    )
    caliber_2 = fields.Float(
        '28-30',
        compute='_compute_caliber_2',
        store=True
    )
    caliber_3 = fields.Float(
        '30-32',
        compute='_compute_caliber_3',
        store=True
    )
    caliber_4 = fields.Float(
        '32-34',
        compute='_compute_caliber_4',
        store=True
    )
    caliber_5 = fields.Float(
        '34-36',
        compute='_compute_caliber_5',
        store=True
    )
    caliber_6 = fields.Float(
        '36+',
        compute='_compute_caliber_6',
        store=True
    )

    @api.model
    def get_caliber(self, name):
        return self.caliber_ids.filtered(lambda a: a.name == name)

    @api.multi
    @api.depends('caliber_ids')
    def _compute_caliber_1(self):
        for item in self:
            item.caliber_1 = item.get_caliber('26-28').percent

    @api.multi
    @api.depends('caliber_ids')
    def _compute_caliber_2(self):
        for item in self:
            item.caliber_2 = item.get_caliber('28-30').percent

    @api.multi
    @api.depends('caliber_ids')
    def _compute_caliber_3(self):
        for item in self:
            item.caliber_3 = item.get_caliber('30-32').percent

    @api.multi
    @api.depends('caliber_ids')
    def _compute_caliber_4(self):
        for item in self:
            item.caliber_4 = item.get_caliber('32-34').percent

    @api.multi
    @api.depends('caliber_ids')
    def _compute_caliber_5(self):
        for item in self:
            item.caliber_5 = item.get_caliber('34-36').percent

    @api.multi
    @api.depends('caliber_ids')
    def _compute_caliber_6(self):
        for item in self:
            item.caliber_6 = item.get_caliber('>36').percent

    external_damage_analysis_ids = fields.One2many(
        'external.damage.analysis',
        'quality_analysis_id',
        'Análisis Daños Externos'
    )

    external_damage_analysis_1 = fields.Float(
        'MANCHA GRAVE',
        compute='_compute_external_damage_analysis_1',
        store=True
    )

    external_damage_analysis_2 = fields.Float(
        'MEZCLA VARIEDAD',
        compute='_compute_external_damage_analysis_2',
        store=True
    )

    external_damage_analysis_3 = fields.Float(
        'CASCO ABIERTO',
        compute='_compute_external_damage_analysis_3',
        store=True
    )

    external_damage_analysis_4 = fields.Float(
        'CÁSCARA IMPERFECTA',
        compute='_compute_external_damage_analysis_4',
        store=True
    )

    external_damage_analysis_5 = fields.Float(
        'NUEZ PARTIDA',
        compute='_compute_external_damage_analysis_5',
        store=True
    )

    external_damage_analysis_6 = fields.Float(
        'NUEZ TRIZADA',
        compute='_compute_external_damage_analysis_6',
        store=True
    )

    external_damage_analysis_7 = fields.Float(
        'PELÓN ADERIDO',
        compute='_compute_external_damage_analysis_7',
        store=True
    )

    external_damage_analysis_8 = fields.Float(
        'HONGO ACTIVO NCC',
        compute='_compute_external_damage_analysis_8',
        store=True
    )

    external_damage_analysis_9 = fields.Float(
        'HONGO INACTIVO NCC',
        compute='_compute_external_damage_analysis_9',
        store=True
    )

    external_damage_analysis_10 = fields.Float(
        'MANCHA LEVE',
        compute='_compute_external_damage_analysis_10',
        store=True
    )

    external_damage_analysis_11 = fields.Float(
        'TIERRA',
        compute='_compute_external_damage_analysis_11',
        store=True
    )

    @api.model
    def get_external_damage(self, name):
        return self.external_damage_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    @api.depends('external_damage_analysis_ids')
    def _compute_external_damage_analysis_1(self):
        for item in self:
            item.external_damage_analysis_1 = item.get_external_damage('MANCHA GRAVE (SERIOUS STAIN)').percent

    @api.multi
    @api.depends('external_damage_analysis_ids')
    def _compute_external_damage_analysis_2(self):
        for item in self:
            item.external_damage_analysis_2 = item.get_external_damage('MEZCLA VARIEDAD (MIX VARIETY)').percent

    @api.multi
    @api.depends('external_damage_analysis_ids')
    def _compute_external_damage_analysis_3(self):
        for item in self:
            item.external_damage_analysis_3 = item.get_external_damage('CASCO ABIERTO (OPEN SHELL)').percent

    @api.multi
    @api.depends('external_damage_analysis_ids')
    def _compute_external_damage_analysis_4(self):
        for item in self:
            item.external_damage_analysis_4 = item.get_external_damage('CÁSCARA IMPERFECTA (IMPERFECT SHELL)').percent

    @api.multi
    @api.depends('external_damage_analysis_ids')
    def _compute_external_damage_analysis_5(self):
        for item in self:
            item.external_damage_analysis_5 = item.get_external_damage('NUEZ PARTIDA (BROKEN SHELL)').percent

    @api.multi
    @api.depends('external_damage_analysis_ids')
    def _compute_external_damage_analysis_6(self):
        for item in self:
            item.external_damage_analysis_6 = item.get_external_damage('NUEZ TRIZADA (CRACKED SHELL)').percent

    @api.multi
    @api.depends('external_damage_analysis_ids')
    def _compute_external_damage_analysis_7(self):
        for item in self:
            item.external_damage_analysis_7 = item.get_external_damage('PELÓN ADHERIDO (ADHERING HULL)').percent

    @api.multi
    @api.depends('external_damage_analysis_ids')
    def _compute_external_damage_analysis_8(self):
        for item in self:
            item.external_damage_analysis_8 = item.get_external_damage('HONGO ACTIVO NCC (DECAY)').percent

    @api.multi
    @api.depends('external_damage_analysis_ids')
    def _compute_external_damage_analysis_9(self):
        for item in self:
            item.external_damage_analysis_9 = item.get_external_damage('HONGO INACTIVO NCC (MOLD)').percent

    @api.multi
    @api.depends('external_damage_analysis_ids')
    def _compute_external_damage_analysis_10(self):
        for item in self:
            item.external_damage_analysis_10 = item.get_external_damage('MANCHA LEVE (SLIGHT STAIN)').percent

    @api.multi
    @api.depends('external_damage_analysis_ids')
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
        compute='_compute_internal_damage_analysis_1',
        store=True
    )

    internal_damage_analysis_2 = fields.Float(
        'DAÑO INSECTO',
        compute='_compute_internal_damage_analysis_2',
        store=True
    )

    internal_damage_analysis_3 = fields.Float(
        'RESECA LEVE',
        compute='_compute_internal_damage_analysis_3',
        store=True
    )

    internal_damage_analysis_4 = fields.Float(
        'HONGO ACTIVO NSC',
        compute='_compute_internal_damage_analysis_4',
        store=True
    )

    internal_damage_analysis_5 = fields.Float(
        'HONGO INACTIVO NSC',
        compute='_compute_internal_damage_analysis_5',
        store=True
    )

    internal_damage_analysis_6 = fields.Float(
        'PULPA NARANJA',
        compute='_compute_internal_damage_analysis_6',
        store=True
    )

    internal_damage_analysis_7 = fields.Float(
        'RANCIDEZ',
        compute='_compute_internal_damage_analysis_7',
        store=True
    )

    @api.model
    def get_internal_damage(self, name):
        return self.internal_damage_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    @api.depends('internal_damage_analysis_ids')
    def _compute_internal_damage_analysis_1(self):
        for item in self:
            item.internal_damage_analysis_1 = item.get_internal_damage('RESECA GRAVE (SERIOUS SHRIVELLING)').percent

    @api.multi
    @api.depends('internal_damage_analysis_ids')
    def _compute_internal_damage_analysis_2(self):
        for item in self:
            item.internal_damage_analysis_2 = item.get_internal_damage('DAÑO INSECTO (INSECT DAMAGE)').percent

    @api.multi
    @api.depends('internal_damage_analysis_ids')
    def _compute_internal_damage_analysis_3(self):
        for item in self:
            item.internal_damage_analysis_3 = item.get_internal_damage('RESECA LEVE (LIGHT SHRIVELLING)').percent

    @api.multi
    @api.depends('internal_damage_analysis_ids')
    def _compute_internal_damage_analysis_4(self):
        for item in self:
            item.internal_damage_analysis_4 = item.get_internal_damage('HONGO ACTIVO NSC (DECAY)').percent

    @api.multi
    @api.depends('internal_damage_analysis_ids')
    def _compute_internal_damage_analysis_5(self):
        for item in self:
            item.internal_damage_analysis_5 = item.get_internal_damage('HONGO INACTIVO NSC (MOLD)').percent

    @api.multi
    @api.depends('internal_damage_analysis_ids')
    def _compute_internal_damage_analysis_6(self):
        for item in self:
            item.internal_damage_analysis_6 = item.get_internal_damage('PULPA NARANJA').percent

    @api.multi
    @api.depends('internal_damage_analysis_ids')
    def _compute_internal_damage_analysis_7(self):
        for item in self:
            item.internal_damage_analysis_7 = item.get_internal_damage('CRISTALINO (RANCID)').percent

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
        compute='_compute_performance_analysis_1',
        store=True
    )

    performance_analysis_2 = fields.Float(
        'Rendimiento Partido Exportable',
        compute='_compute_performance_analysis_2',
        store=True
    )

    @api.model
    def get_performance(self, name):
        return self.performance_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    @api.depends('performance_analysis_ids')
    def _compute_performance_analysis_1(self):
        for item in self:
            item.performance_analysis_1 = item.get_performance('RENDIMIENTO PARTIDO TOTAL').percent

    @api.multi
    @api.depends('performance_analysis_ids')
    def _compute_performance_analysis_2(self):
        for item in self:
            item.performance_analysis_2 = item.get_performance('RENDIMIENTO PARTIDO EXPORTABLE').percent

    color_analysis_ids = fields.One2many(
        'color.analysis',
        'quality_analysis_id',
        'Análisis Color'
    )

    color_analysis_1 = fields.Float(
        'EXTRA LIGHT',
        compute='_compute_color_analysis_1',
        store=True
    )

    color_analysis_2 = fields.Float(
        'EXTRA LIGHT FANCY',
        compute='_compute_color_analysis_2',
        store=True
    )

    color_analysis_3 = fields.Float(
        'EXTRA LIGHT STANDAR',
        compute='_compute_color_analysis_3',
        store=True
    )

    color_analysis_4 = fields.Float(
        'LIGHT',
        compute='_compute_color_analysis_4',
        store=True
    )

    color_analysis_5 = fields.Float(
        'LIGHT AMBER',
        compute='_compute_color_analysis_5',
        store=True
    )

    color_analysis_6 = fields.Float(
        'AMBER',
        compute='_compute_color_analysis_6',
        store=True
    )

    color_analysis_7 = fields.Float(
        'AMARILLA',
        compute='_compute_color_analysis_7',
        store=True
    )

    @api.model
    def get_color(self, name):
        return self.color_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    @api.depends('color_analysis_ids')
    def _compute_color_analysis_1(self):
        for item in self:
            item.color_analysis_1 = item.get_color('EXTRA LIGHT').percent

    @api.multi
    @api.depends('color_analysis_ids')
    def _compute_color_analysis_2(self):
        for item in self:
            item.color_analysis_2 = item.get_color('EXTRA LIGHT FANCY').percent

    @api.multi
    @api.depends('color_analysis_ids')
    def _compute_color_analysis_3(self):
        for item in self:
            item.color_analysis_3 = item.get_color('EXTRA LIGHT STANDARD').percent

    @api.multi
    @api.depends('color_analysis_ids')
    def _compute_color_analysis_4(self):
        for item in self:
            item.color_analysis_4 = item.get_color('LIGHT').percent

    @api.multi
    @api.depends('color_analysis_ids')
    def _compute_color_analysis_5(self):
        for item in self:
            item.color_analysis_5 = item.get_color('LIGHT AMBER').percent

    @api.multi
    @api.depends('color_analysis_ids')
    def _compute_color_analysis_6(self):
        for item in self:
            item.color_analysis_6 = item.get_color('AMBER').percent

    @api.multi
    @api.depends('color_analysis_ids')
    def _compute_color_analysis_7(self):
        for item in self:
            item.color_analysis_7 = item.get_color('AMARIILA (YELLOW)').percent

    form_analysis_ids = fields.One2many(
        'form.analysis',
        'quality_analysis_id',
        'Análisis Forma'
    )

    form_analysis_1 = fields.Float(
        'HALVES 7/8',
        compute='_compute_form_analysis_1',
        store=True
    )

    form_analysis_2 = fields.Float(
        'QUARTERS',
        compute='_compute_form_analysis_2',
        store=True
    )

    form_analysis_3 = fields.Float(
        'PIECES',
        compute='_compute_form_analysis_3',
        store=True
    )

    form_analysis_4 = fields.Float(
        'HALVES 3/4',
        compute='_compute_form_analysis_4',
        store=True
    )

    @api.model
    def get_form(self, name):
        return self.form_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    @api.depends('form_analysis_ids')
    def _compute_form_analysis_1(self):
        for item in self:
            item.form_analysis_1 = item.get_form('HALVES 7/8').percent

    @api.multi
    @api.depends('form_analysis_ids')
    def _compute_form_analysis_2(self):
        for item in self:
            item.form_analysis_2 = item.get_form('QUARTERS').percent

    @api.multi
    @api.depends('form_analysis_ids')
    def _compute_form_analysis_3(self):
        for item in self:
            item.form_analysis_3 = item.get_form('PIECES').percent

    @api.multi
    @api.depends('form_analysis_ids')
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
        compute='_compute_impurity_analysis_1',
        store=True
    )

    impurity_analysis_2 = fields.Float(
        'SEPTUM',
        compute='_compute_impurity_analysis_2',
        store=True
    )

    impurity_analysis_3 = fields.Float(
        'FOREIGN MATERIAL',
        compute='_compute_impurity_analysis_3',
        store=True
    )

    @api.model
    def get_impurity(self, name):
        return self.impurity_analysis_ids.filtered(lambda a: a.name == name)

    @api.multi
    @api.depends('impurity_analysis_ids')
    def _compute_impurity_analysis_1(self):
        for item in self:
            item.impurity_analysis_1 = item.get_impurity('SHELL').percent

    @api.multi
    @api.depends('impurity_analysis_ids')
    def _compute_impurity_analysis_2(self):
        for item in self:
            item.impurity_analysis_2 = item.get_impurity('SEPTUM').percent

    @api.multi
    @api.depends('impurity_analysis_ids')
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


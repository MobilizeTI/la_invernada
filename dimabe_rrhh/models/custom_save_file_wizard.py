from odoo import fields

class CustomSaveFileWizard(models.TransientModel):
    _name = 'custom.save.file.wizard'

    file = fields.Binary('Archivo', readonly=True)
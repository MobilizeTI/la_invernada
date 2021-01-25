from odoo import fields

class CustomSaveFileWizard(models.TransientModel):
    _name = 'custom.save.file.wizard'

    file = fields.Binary('Archivo', readonly=True)

    file_name = fields.Char('Nombre del archivo', readonly=True)
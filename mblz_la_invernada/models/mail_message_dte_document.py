import logging

_logger = logging.getLogger(__name__)

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _
from lxml import etree
from collections import defaultdict

try:
    from io import BytesIO
except ImportError:
    _logger.warning("no se ha cargado io")
try:
    import pdf417gen
except ImportError:
    _logger.warning("Cannot import pdf417gen library")
try:
    import base64
except ImportError:
    _logger.warning("Cannot import base64 library")
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    _logger.warning("no se ha cargado PIL")


class ProcessMailsDocument(models.Model):
    _inherit = "mail.message.dte.document"

    attachment_pdf_ids = fields.Many2many('ir.attachment',
                                          string='Attachments',
                                          compute='_compute_attachment_pdf_ids')

    @api.multi
    @api.depends('dte_id')
    def _compute_attachment_pdf_ids(self):
        for rec in self:
            if rec.dte_id and rec.dte_id.mail_id and rec.dte_id.mail_id.attachment_ids:
                pdf_attach = []
                for att in rec.dte_id.mail_id.attachment_ids:
                    if att.mimetype in ["application/pdf"]:
                        pdf_attach.append(att.id)
                rec.attachment_pdf_ids = [(6, 0, pdf_attach)]

    sii_barcode = fields.Char(
        copy=False,
        string=_("SII Barcode"), compute='_compute_sii_barcode'
    )

    @api.multi
    @api.depends('xml')
    def _compute_sii_barcode(self):
        for rec in self:
            if rec.xml:
                root = etree.fromstring(rec.xml)
                ted_element = root.xpath("//Documento/TED")
                rec.sii_barcode = etree.tostring(ted_element[0], encoding='utf-8')

    sii_barcode_img = fields.Binary(
        string=_("SII Barcode Image"),
        help="SII Barcode Image in PDF417 format",
        compute="_get_barcode_img",
    )

    def pdf417bc(self, ted, columns=13, ratio=3):
        bc = pdf417gen.encode(
            ted,
            security_level=5,
            columns=columns,
            encoding='ISO-8859-1',
        )
        image = pdf417gen.render_image(
            bc,
            padding=15,
            scale=1,
            ratio=ratio,
        )
        return image

    @api.multi
    def get_barcode_img(self, columns=13, ratio=3):
        barcodefile = BytesIO()
        image = self.pdf417bc(self.sii_barcode, columns, ratio)
        image.save(barcodefile, "PNG")
        data = barcodefile.getvalue()
        return base64.b64encode(data)

    def _get_barcode_img(self):
        for r in self:
            if r.sii_barcode:
                r.sii_barcode_img = r.get_barcode_img()

    @api.model
    def default_get(self, default_fields):
        res = super(ProcessMailsDocument, self).default_get(default_fields)
        currency_id = self.env['res.users'].browse(self._uid).company_id.currency_id
        if currency_id:
            res.update({
                'currency_id': currency_id.id,
                'company_id': self.env.user.company_id.id
            })
        return res

    def etree_to_dict(self, t):
        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(self.etree_to_dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
        if t.attrib:
            d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[t.tag]['#text'] = text
            else:
                d[t.tag] = text
        return d

    def _receptor_data(self):
        Receptor = {'RUTRecep': self.get_doc_rut()}
        if self.new_partner:
            p = self.new_partner.split(' ')
            Receptor['RznSocRecep'] = ' '.join(p[1:])
        else:
            commercial_partner_id = self.partner_id.commercial_partner_id or self.partner_id
            Receptor['RznSocRecep'] = commercial_partner_id.name
        return Receptor

    def _document_data(self):
        if self.xml:
            root = etree.fromstring(self.xml)
            dict_xml = self.etree_to_dict(root)
            document = dict_xml.get('DTE').get('Documento')
            details = document.get('Detalle')
            if isinstance(details, dict):
                new_details = [details]
                document.update({'Detalle': new_details})
            return document

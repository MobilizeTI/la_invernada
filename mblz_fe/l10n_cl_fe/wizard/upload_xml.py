import base64
import logging

from facturacion_electronica import facturacion_electronica as fe
from lxml import etree

from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class UploadXMLWizard(models.TransientModel):
    _name = "sii.dte.upload_xml.wizard"
    _description = "SII XML from Provider"

    action = fields.Selection(
        [("create_po", "Crear Orden de Pedido y Factura"), ("create", "Crear Solamente Factura"),],
        string="Acción",
        default="create",
    )
    xml_file = fields.Binary(string="XML File", filters="*.xml", store=True, help="Upload the XML File in this holder",)
    filename = fields.Char(string="File Name",)
    pre_process = fields.Boolean(default=True,)
    dte_id = fields.Many2one("mail.message.dte", string="DTE",)
    document_id = fields.Many2one("mail.message.dte.document", string="Documento",)
    option = fields.Selection(
        [("upload", "Solo Subir"), ("accept", "Aceptar"), ("reject", "Rechazar"),], string="Opción",
    )
    num_dtes = fields.Integer(string="Número de DTES", readonly=True,)
    type = fields.Selection(
        [("ventas", "Ventas"), ("compras", "Compras"),], string="Tipo de Operación", default="compras",
    )

    @api.onchange("xml_file")
    def get_num_dtes(self):
        if self.xml_file:
            self.num_dtes = len(self._get_dtes())

    @api.multi
    def confirm(self, ret=False):
        created = []
        if self.document_id:
            self.dte_id = self.document_id.dte_id.id
        if not self.dte_id:
            dte_id = self.env["mail.message.dte"].search([("name", "=", self.filename),], limit=1,)
            if not dte_id:
                dte = {
                    "name": self.filename,
                }
                dte_id = self.env["mail.message.dte"].create(dte)
            self.dte_id = dte_id
        if self.type == "ventas":
            created = self.do_create_inv()
            xml_id = "account.action_vendor_bill_template"
            target_model = "account.invoice"
        elif self.pre_process or self.action == "upload":
            created = self.do_create_pre()
            xml_id = "l10n_cl_fe.action_dte_process"
            target_model = "mail.message.dte"
        elif self.option == "reject":
            self.do_reject()
            return
        elif self.action == "create":
            created = self.do_create_inv()
            xml_id = "account.action_vendor_bill_template"
            target_model = "account.invoice"
        if self.action == "create_po":
            self.do_create_po()
            xml_id = "purchase.purchase_order_tree"
            target_model = "purchase.order"
        if ret:
            return created
        return {
            "type": "ir.actions.act_window",
            "name": _("List of Results"),
            "view_type": "form" if self.dte_id else "tree",
            "view_mode": "tree",
            "res_model": target_model,
            "domain": str([("id", "in", created)]),
            "views": [(self.env.ref("%s" % xml_id).id, "tree")],
            "target": "current",
        }

    def format_rut(self, RUTEmisor=None):
        rut = RUTEmisor.replace("-", "")
        rut = "CL" + rut
        return rut

    def _get_xml(self):
        if self.document_id:
            xml = self.document_id.xml
        elif self.xml_file:
            xml = base64.b64decode(self.xml_file).decode("ISO-8859-1")
        return xml

    def _get_xml_name(self):
        return self.dte_id.name or self.filename

    def _read_xml(self, mode="text", check=False):
        xml = (
            self._get_xml()
            .replace('<?xml version="1.0" encoding="ISO-8859-1"?>', "")
            .replace('<?xml version="1.0" encoding="ISO-8859-1" ?>', "")
        )
        if check:
            return xml
        xml = xml.replace(' xmlns="http://www.sii.cl/SiiDte"', "")
        if mode == "etree":
            parser = etree.XMLParser(remove_blank_text=True)
            return etree.fromstring(xml, parser=parser)
        return xml

    def _get_datos_empresa(self, company_id):
        firma = self.env.user.get_digital_signature(company_id)
        return {
            "Emisor": {
                "RUTEmisor": company_id.partner_id.rut(),
                "Modo": "produccion" if company_id.dte_service_provider == "SII" else "certificacion",
            },
            "firma_electronica": firma.parametros_firma(),
        }

    def _create_attachment(self, xml, name, id=False, model="account.invoice"):
        data = base64.b64encode(xml.encode("ISO-8859-1"))
        filename = (name + ".xml").replace(" ", "")
        url_path = "/download/xml/resp/%s" % (id)
        att = self.env["ir.attachment"].search(
            [("name", "=", filename), ("res_id", "=", id), ("res_model", "=", model)], limit=1
        )
        if att:
            return att
        values = dict(
            name=filename, datas_fname=filename, url=url_path, res_model=model, res_id=id, type="binary", datas=data,
        )
        att = self.env["ir.attachment"].create(values)
        return att

    def do_receipt_deliver(self):
        envio = self._read_xml("etree")
        if envio.find("SetDTE") is None or envio.find("SetDTE/Caratula") is None:
            return True
        company_id = self.env["res.company"].search(
            [("vat", "=", self.format_rut(envio.find("SetDTE/Caratula/RutReceptor").text))], limit=1
        )
        IdRespuesta = self.env.ref("l10n_cl_fe.response_sequence").next_by_id()
        vals = self._get_datos_empresa(company_id)
        vals.update(
            {
                "Recepciones": [
                    {
                        "IdRespuesta": IdRespuesta,
                        "RutResponde": company_id.partner_id.rut(),
                        "NmbContacto": self.env.user.partner_id.name,
                        "FonoContacto": self.env.user.partner_id.phone,
                        "MailContacto": self.env.user.partner_id.email,
                        "xml_nombre": self._get_xml_name(),
                        "xml_envio": self._get_xml(),
                    }
                ]
            }
        )
        respuesta = fe.leer_xml(vals)
        if self.dte_id:
            for r in respuesta:
                att = self._create_attachment(r["respuesta_xml"], r["nombre_xml"], self.dte_id.id, "mail.message.dte")
                dte_email_id = self.dte_id.company_id.dte_email_id or self.env.user.company_id.dte_email_id
                email_to = self.sudo().dte_id.mail_id.email_from
                if envio is not None:
                    RUT = envio.find("SetDTE/Caratula/RutEmisor").text
                    partner_id = self.env["res.partner"].search(
                        [("active", "=", True), ("parent_id", "=", False), ("vat", "=", self.format_rut(RUT))]
                    )
                    if partner_id.dte_email:
                        email_to = partner_id.dte_email
                values = {
                    "res_id": self.dte_id.id,
                    "email_from": dte_email_id.name_get(),
                    "email_to": email_to,
                    "auto_delete": False,
                    "model": "mail.message.dte",
                    "body": "XML de Respuesta Envío, Estado: %s , Glosa: %s "
                    % (r["EstadoRecepEnv"], r["RecepEnvGlosa"]),
                    "subject": "XML de Respuesta Envío",
                    "attachment_ids": [[6, 0, att.ids]],
                }
                send_mail = self.env["mail.mail"].sudo().create(values)
                send_mail.send()

    def _get_data_partner(self, data):
        if self.pre_process and self.type == "compras":
            return False
        type = "Emis"
        if self.type == "ventas":
            type = "Recep"
            if data.find("RUT%s" % type).text in [False, "66666666-6", "00000000-0"]:
                return self.env.ref("l10n_cl_fe.par_cfa")
        el = data.find("Giro%s" % type)
        if el is None:
            giro = "Boleta"
        else:
            giro = el.text
        giro_id = self.env["sii.activity.description"].search([("name", "=", giro)])
        if not giro_id:
            giro_id = self.env["sii.activity.description"].create({"name": giro,})
        type = "Emisor"
        dest = "Origen"
        rut_path = "RUTEmisor"
        if self.type == "ventas":
            type = "Receptor"
            dest = "Recep"
            rut_path = "RUTRecep"
        rut = self.format_rut(data.find(rut_path).text)
        name = (
            (data.find("RznSoc").text or data.find("RznSocEmisor").text)
            if self.type == "compras"
            else data.find("RznSocRecep").text
        )
        city_id = self.env["res.city"].search([("name", "=", data.find("Cmna%s" % dest).text.title())])
        ciudad = data.find("Ciudad%s" % dest)
        partner = {
            "name": name,
            "activity_description": giro_id.id,
            "vat": rut,
            "document_type_id": self.env.ref("l10n_cl_fe.dt_RUT").id,
            "responsability_id": self.env.ref("l10n_cl_fe.res_IVARI").id,
            "document_number": data.find(rut_path).text,
            "street": data.find("Dir%s" % dest).text,
            "city": ciudad.text if ciudad is not None else city_id.name,
            "company_type": "company",
            "city_id": city_id.id,
            "country_id": self.env.ref('base.cl').id,
            'es_mipyme': False,
        }
        if data.find("CorreoEmisor") is not None or data.find("CorreoRecep") is not None:
            partner.update(
                {
                    "email": data.find("CorreoEmisor").text
                    if self.type == "compras"
                    else data.find("CorreoRecep").text,
                    "dte_email": data.find("CorreoEmisor").text
                    if self.type == "compras"
                    else data.find("CorreoRecep").text,
                }
            )
            if '@sii.cl' in partner['dte_email'].lower():
                del partner['dte_email']
                partner['es_mipyme'] = True
        return partner

    def _create_partner(self, data):
        partner_id = False
        partner = self._get_data_partner(data)
        if partner:
            if self.type == "compras":
                partner.update({"supplier": True})
            partner_id = self.env["res.partner"].create(partner)
        return partner_id

    def _default_category(self):
        md = self.env["ir.model.data"]
        res = False
        try:
            res = md.get_object_reference("product", "product_category_all")[1]
        except ValueError:
            res = False
        return res

    def _buscar_impuesto(self, type="purchase", name="Impuesto", amount=0,
                         sii_code=0, sii_type=False, IndExe=None,
                         company_id=False):
        #TODO impuesto retencion
        _logger.info('LOG:  buscar impuesto {} sii_code {}'.format(company_id, sii_code))
        query = [
            ("amount", "=", amount),
            ("sii_code", "=", sii_code),
            ("type_tax_use", "=", type),
            ("activo_fijo", "=", False),
            ("company_id", "=", company_id.id),
        ]
        if IndExe is not None:
            query.append(("sii_type", "=", False))
        if amount == 0 and sii_code == 0 and IndExe is None:
            query.append(("name", "=", name))
        if sii_type:
            query.extend(
                [("sii_type", "=", sii_type),]
            )
        imp = self.env["account.tax"].search(query)
        if not imp:
            imp = (
                self.env["account.tax"]
                .sudo()
                .create(
                    {
                        "amount": amount,
                        "name": name,
                        "sii_code": sii_code,
                        "sii_type": sii_type,
                        "type_tax_use": type,
                        "company_id": company_id.id,
                    }
                )
            )
        return imp

    def get_product_values(self, line, company_id, price_included=False, exenta=False):
        IndExe = line.find("IndExe")
        amount = 0
        sii_code = 0
        sii_type = False
        if IndExe is None and not exenta:
            amount = 19
            sii_code = 14
            sii_type = False
        else:
            IndExe = True
        imp = self._buscar_impuesto(amount=amount,
                                    type="purchase",
                                    sii_code=sii_code,
                                    sii_type=sii_type,
                                    IndExe=IndExe,
                                    company_id=company_id)
        imp_sale = self._buscar_impuesto(amount=amount,
                                    type="sale",
                                    sii_code=sii_code,
                                    sii_type=sii_type,
                                    IndExe=IndExe,
                                    company_id=company_id)
        price = float(line.find("PrcItem").text if line.find("PrcItem") is not None else line.find("MontoItem").text)
        if price_included:
            price = imp.compute_all(price, self.env.user.company_id.currency_id, 1)["total_excluded"]
        values = {
            "sale_ok": (self.type == "ventas"),
            "name": line.find("NmbItem").text,
            "lst_price": price,
            "categ_id": self._default_category(),
            "taxes_id": [(6, 0, imp_sale.ids)],
            "supplier_taxes_id": [(6, 0, imp.ids)],
        }
        for c in line.findall("CdgItem"):
            VlrCodigo = c.find("VlrCodigo").text
            if c.find("TpoCodigo").text == "ean13":
                values["barcode"] = VlrCodigo
            else:
                values["default_code"] = VlrCodigo
        return values

    def _create_prod(self, data, company_id, price_included=False, exenta=False):
        product_id = self.env["product.product"].create(
            self.get_product_values(data, company_id, price_included, exenta)
        )
        return product_id

    def _buscar_producto(self, document_id, line, company_id, price_included=False, exenta=False):
        default_code = False
        CdgItem = line.find("CdgItem")
        NmbItem = line.find("NmbItem").text
        if NmbItem.isspace():
            NmbItem = "Producto Genérico"
        if document_id:
            code = " " + etree.tostring(CdgItem).decode() if CdgItem is not None else ""
            line_id = self.env["mail.message.dte.document.line"].search(
                [("sequence", "=", line.find("NroLinDet").text), ("document_id", "=", document_id.id),]
            )
            if line_id:
                if line_id.product_id:
                    return line_id.product_id.id
        query = False
        product_id = False
        if CdgItem is not None:
            for c in line.findall("CdgItem"):
                VlrCodigo = c.find("VlrCodigo")
                if VlrCodigo is None or VlrCodigo.text is None or VlrCodigo.text.isspace():
                    continue
                TpoCodigo = c.find("TpoCodigo").text
                if TpoCodigo == "ean13":
                    query = [("barcode", "=", VlrCodigo.text)]
                elif TpoCodigo == "INT1":
                    query = [("default_code", "=", VlrCodigo.text)]
                default_code = VlrCodigo.text
        if not query:
            query = [("name", "=", NmbItem)]
        product_id = self.env["product.product"].search(query)
        query2 = [("name", "=", document_id.partner_id.id)]
        if default_code:
            query2.append(("product_code", "=", default_code))
        else:
            query2.append(("product_name", "=", NmbItem))
        product_supplier = False
        if not product_id and self.type == "compras":
            product_supplier = self.env["product.supplierinfo"].search(query2)
            if product_supplier and not product_supplier.product_tmpl_id.active:
                raise UserError(_("Plantilla Producto para el proveedor marcado como archivado"))
            product_id = product_supplier.product_id or product_supplier.product_tmpl_id.product_variant_id
            if not product_id:
                if not self.pre_process:
                    product_id = self._create_prod(line, company_id, price_included, exenta)
                else:
                    code = ""
                    coma = ""
                    for c in line.findall("CdgItem"):
                        code += coma + c.find("TpoCodigo").text + " " + c.find("VlrCodigo").text
                        coma = ", "
                    return NmbItem + "" + code
        elif self.type == "ventas" and not product_id:
            product_id = self._create_prod(line, company_id, price_included, exenta)
        if not product_supplier and document_id.partner_id and self.type == "compras":
            price = float(
                line.find("PrcItem").text if line.find("PrcItem") is not None else line.find("MontoItem").text
            )
            if price_included:
                price = product_id.supplier_taxes_id.compute_all(price, self.env.user.company_id.currency_id, 1)[
                    "total_excluded"
                ]
            supplier_info = {
                "name": document_id.partner_id.id,
                "product_name": NmbItem,
                "product_code": default_code,
                "product_tmpl_id": product_id.product_tmpl_id.id,
                "price": price,
                "product_id": product_id.id,
            }
            self.env["product.supplierinfo"].create(supplier_info)
        if not product_id.active:
            raise UserError(_("Producto para el proveedor marcado como archivado"))
        return product_id.id

    def _prepare_line(self, line, document_id, type, company_id, fpos_id, price_included=False, exenta=False):
        data = {}
        _logger.info('LOG ***** en preparar la lineas')
        product_id = self._buscar_producto(document_id, line, company_id, price_included, exenta)
        if isinstance(product_id, int):
            data.update(
                {
                    "product_id": product_id,
                    
                    }
            )
        elif not product_id:
            return False
        # elif isinstance(product_id, str):
        #     data.update({
        #         "name": product_id,
        #     })
            
        price_subtotal = float(line.find("MontoItem").text)
        discount = 0
        if line.find("DescuentoPct") is not None:
            discount = float(line.find("DescuentoPct").text)
        price = float(line.find("PrcItem").text) if line.find("PrcItem") is not None else price_subtotal
        DscItem = line.find("DscItem")
        _logger.info('LOG:  ******* prodcut_id {}'.format(product_id))
        ##TODO urgente ver la forma de traer correctamente el producto
        data.update(
            {
                "sequence": line.find("NroLinDet").text,
                # "name": DscItem.text if DscItem is not None else line.find("NmbItem").text,
                "name": product_id,
                "price_unit": price,
                "discount": discount,
                "quantity": line.find("QtyItem").text if line.find("QtyItem") is not None else 1,
                "price_subtotal": price_subtotal,
            }
        )
        if self.pre_process and self.type == "compras":
            data.update(
                {"new_product": product_id, "product_description": DscItem.text if DscItem is not None else "",}
            )
        else:
            product_id = self.env["product.product"].browse(product_id)
            fpos = self.env["account.fiscal.position"].browse(fpos_id)
            account = self.env["account.invoice.line"].get_invoice_line_account(type, product_id, fpos, company_id)
            IndExe = line.find("IndExe")
            amount = 0
            sii_code = 0
            sii_type = False
            tax_ids = self.env["account.tax"]
            if IndExe is None and not exenta:
                amount = 19
                sii_code = 14
                sii_type = False
            else:
                IndExe = True
            tax_ids += self._buscar_impuesto(
                type="purchase" if self.type == "compras" else "sale",
                amount=amount, sii_code=sii_code, sii_type=sii_type,
                IndExe=IndExe, company_id=company_id
            )
            if line.find("CodImpAdic") is not None:
                amount = 19
                sii_type = False
                tax_ids += self._buscar_impuesto(
                    type="purchase" if self.type == "compras" else "sale",
                    amount=amount, sii_code=line.find("CodImpAdic").text,
                    sii_type=sii_type, IndExe=IndExe, company_id=company_id
                )
            if IndExe is None:
                tax_include = False
                for t in tax_ids:
                    if not tax_include:
                        tax_include = t.price_include
                if price_included and not tax_include:
                    base = price
                    price = 0
                    base_subtotal = price_subtotal
                    price_subtotal = 0
                    for t in tax_ids:
                        if t.amount > 0:
                            price += base / (1 + (t.amount / 100.0))
                            price_subtotal += base_subtotal / (1 + (t.amount / 100.0))
                elif not price_included and tax_include:
                    price = tax_ids.compute_all(price, self.env.user.company_id.currency_id, 1)["total_included"]
                    price_subtotal = tax_ids.compute_all(price_subtotal, self.env.user.company_id.currency_id, 1)[
                        "total_included"
                    ]
            _logger.info('LOG:   producto {}'.format(product_id.categ_id.property_account_expense_categ_id.id))
            data.update(
                {
                    "account_id": 4355,
                    # "account_id": product_id.product_tmpl_id.categ_id.property_account_expense_categ_id.id,
                    "invoice_line_tax_ids": [(6, 0, tax_ids.ids)],
                    "uom_id": product_id.uom_id.id,
                    "price_unit": price,
                    "price_subtotal": price_subtotal,
                }
            )
        _logger.info('LOG: line_data {}'.format(data))
        _logger.info('LOG:: prodcut {}'.format(product_id))
        return [0, 0, data]

    def _create_tpo_doc(self, TpoDocRef, RazonRef=None):
        vals = dict(name=str(TpoDocRef))
        if RazonRef is not None:
            vals["name"] = "{} {}".format(vals["name"], RazonRef.text)
        if str(TpoDocRef).isdigit():
            vals.update(
                {"sii_code": TpoDocRef,}
            )
        else:
            vals.update(
                {"doc_code_prefix": TpoDocRef, "sii_code": 801, "use_prefix": True,}
            )
        return self.env["sii.document_class"].create(vals)

    def _prepare_ref(self, ref):
        query = []
        TpoDocRef = ref.find("TpoDocRef").text
        RazonRef = ref.find("RazonRef")
        if str(TpoDocRef).isdigit():
            query.append(("sii_code", "=", TpoDocRef))
            query.append(("use_prefix", "=", False))
        else:
            query.append(("doc_code_prefix", "=", TpoDocRef))
        tpo = self.env["sii.document_class"].search(query, limit=1)
        if not tpo:
            tpo = self._create_tpo_doc(TpoDocRef, RazonRef)
        return [
            0,
            0,
            {
                "origen": ref.find("FolioRef").text,
                "sii_referencia_TpoDocRef": tpo.id,
                "sii_referencia_CodRef": ref.find("CodRef").text if ref.find("CodRef") is not None else None,
                "motivo": RazonRef.text if RazonRef is not None else None,
                "fecha_documento": ref.find("FchRef").text if ref.find("FchRef") is not None else None,
            },
        ]

    def process_dr(self, dr):
        data = {
            "type": dr.find("TpoMov").text,
        }
        disc_type = "percent"
        if dr.find("TpoValor").text == "$":
            disc_type = "amount"
        data["gdr_type"] = disc_type
        data["valor"] = dr.find("ValorDR").text
        data["gdr_detail"] = dr.find("GlosaDR").text if dr.find("GlosaDR") is not None else "Descuento globla"
        return data

    def _prepare_invoice(self, documento, company_id, journal_id):
        type = "Emisor"
        rut_path = "RUTEmisor"
        if self.type == "ventas":
            type = "Receptor"
            rut_path = "RUTRecep"
        Encabezado = documento.find("Encabezado")
        IdDoc = Encabezado.find("IdDoc")
        Emisor = Encabezado.find(type)
        RUT = Emisor.find(rut_path).text
        invoice = {
            "account_id": False,
        }
        partner_id = self.env["res.partner"].search(
            [("active", "=", True), ("parent_id", "=", False), ("vat", "=", self.format_rut(RUT))]
        )
        _logger.info('LOF:-- partner')
        if not partner_id:
            partner_id = self._create_partner(Encabezado.find("%s" % type))
        elif not partner_id.supplier and self.type == "compras":
            partner_id.supplier = True
        invoice["type"] = "in_invoice"
        if self.type == "ventas":
            invoice["type"] = "out_invoice"
        if IdDoc.find("TipoDTE").text in ["54", "61"]:
            invoice["type"] = "in_refund"
            if self.type == "ventas":
                invoice["type"] = "out_refund"
        if partner_id:
            if journal_id:
                _logger.info('LOG: antes del jorunal')
                account_id = partner_id.property_account_payable_id.id or journal_id.default_debit_account_id.id
                _logger.info('LOG: despues de accpunt')
                if invoice["type"] in ("out_invoice", "in_refund"):
                    account_id = partner_id.property_account_receivable_id.id or journal_id.default_credit_account_id.id
                fpos = self.env["account.fiscal.position"].get_fiscal_position(
                    partner_id.id, delivery_id=partner_id.address_get(["delivery"])["delivery"]
                )
                invoice.update(
                    {"fiscal_position": fpos.id if fpos else False, "account_id": account_id,}
                )
            partner_id = partner_id.id
        try:
            _logger.info('LOG -- >> filename {}'.format(self.filename))
            # name = self.filename.decode("ISO-8859-1").encode("UTF-8")
            name = self.filename
        except Exception as ex:
            _logger.error(tools.ustr(ex))
            name = self.filename.encode("UTF-8")
        ted_string = b""
        if documento.find("TED") is not None:
            ted_string = etree.tostring(documento.find("TED"), method="c14n", pretty_print=False)
        FchEmis = IdDoc.find("FchEmis").text
        # xml_envio = self.env['sii.xml.envio'].create(
        #    {
        #        'name': 'ENVIO_%s' % name.decode(),
        #        'xml_envio': etree.tostring(dte),
        #        'state': 'Aceptado',
        #    }
        # )
        invoice.update(
            {
                # "origin": "XML Envío: " + name.decode(),
                "origin": "XML Envío: " + name,
                "date_invoice": FchEmis,
                "partner_id": partner_id,
                "company_id": company_id.id,
                # 'sii_xml_request': xml_envio.id,
                "sii_xml_dte": "<DTE>%s</DTE>" % etree.tostring(documento).decode('ISO-8859-1'),
                "sii_barcode": ted_string.decode(),
            }
        )
        if journal_id:
            invoice["journal_id"] = journal_id.id
        DscRcgGlobal = documento.findall("DscRcgGlobal")
        if DscRcgGlobal:
            drs = [(5,)]
            for dr in DscRcgGlobal:
                drs.append((0, 0, self.process_dr(dr)))
            invoice.update(
                {"global_descuentos_recargos": drs,}
            )
        Folio = IdDoc.find("Folio").text
        dc_id = self.env["sii.document_class"].search([("sii_code", "=", IdDoc.find("TipoDTE").text)])
        invoice.update(
            {"sii_document_number": Folio, "document_class_id": dc_id.id, 'use_documents': False}
        )
        if self.type == "ventas":
            invoice.update(
                {"move_name": "{}{}".format(dc_id.doc_code_prefix, Folio),}
            )
        else:
            RznSoc = Emisor.find("RznSoc")
            if RznSoc is None:
                RznSoc = Emisor.find("RznSocEmisor")
            invoice.update(
                {
                    "number": Folio,
                    "date": FchEmis,
                    "new_partner": RUT + " " + RznSoc.text,
                    "amount": Encabezado.find("Totales/MntTotal").text,
                }
            )
        return invoice

    def _get_journal(self, sii_code, company_id, ignore_journal=False):
        _logger.info('LOG: get journal')
        dc_id = self.env["sii.document_class"].search([("sii_code", "=", sii_code)])
        type = "purchase"
        if self.type == "ventas":
            type = "sale"
        journal_id = self.env["account.journal"].search(
            [("document_class_ids", "=", dc_id.id), ("type", "=", type), ("company_id", "=", company_id.id),], limit=1,
        )
        if not journal_id and not ignore_journal:
            raise UserError(
                "No existe Diario para el tipo de documento %s, por favor añada uno primero, o ignore el documento"
                % dc_id.name.encode("UTF-8")
            )
        return journal_id

    def _get_invoice_lines(self, documento, document_id, invoice_type, fpos, price_included, company_id):
        _logger.info('LOG**** emn get incoice ñines')
        exenta = documento.find("Encabezado/IdDoc/TipoDTE").text in ["34", "41"]
        lines = []
        for line in documento.findall("Detalle"):
            new_line = self._prepare_line(line, document_id, invoice_type, company_id, fpos, price_included, exenta)
            if new_line:
                lines.append(new_line)
        return lines

    def _get_data(self, documento, company_id, ignore_journal=False):
        _logger.info('LOG: get data')
        Encabezado = documento.find("Encabezado")
        IdDoc = Encabezado.find("IdDoc")
        price_included = Encabezado.find("MntBruto")
        journal_id = self._get_journal(IdDoc.find("TipoDTE").text, company_id, ignore_journal)
        _logger.info('LOG: -->> journal {}'.format(journal_id))
        data = self._prepare_invoice(documento, company_id, journal_id)
        lines = [(5,)]
        document_id = self._dte_exist(documento)
        _logger.info('LOGG********** despies de document_id')
        lines.extend(
            self._get_invoice_lines(
                documento, document_id, data["type"], data.get("fiscal_position", False), price_included, company_id
            )
        )
        product_id = (
            self.env["product.product"].search([("product_tmpl_id", "=", self.env.ref("l10n_cl_fe.product_imp").id)]).id
        )
        _logger.info('LOG: antes del encabezado')
        if Encabezado.find("Totales/ImptoReten") is not None:
            ImptoReten = Encabezado.findall("Totales/ImptoReten")
            for i in ImptoReten:
                imp = self._buscar_impuesto(
                    type="purchase" if self.type == "compras" else "sale",
                    name="OtrosImps_" + i.find("TipoImp").text,
                    sii_code=i.find("TipoImp").text)
                price = float(i.find("MontoImp").text)
                price_subtotal = float(i.find("MontoImp").text)
                if price_included:
                    price = imp.compute_all(price, self.env.user.company_id.currency_id, 1)["total_excluded"]
                    price_subtotal = imp.compute_all(price_subtotal, self.env.user.company_id.currency_id, 1)[
                        "total_excluded"
                    ]
                lines.append(
                    [
                        0,
                        0,
                        {
                            "invoice_line_tax_ids": ((6, 0, imp.ids)),
                            "product_id": product_id,
                            # "name": "MontoImpuesto %s" % i.find("TipoImp").text,
                            "name": product_id.name,
                            "price_unit": price,
                            "quantity": 1,
                            "price_subtotal": price_subtotal,
                            # 'account_id':
                        },
                    ]
                )
        # if 'IVATerc' in dte['Encabezado']['Totales']:
        #    imp = self._buscar_impuesto(name="IVATerc" )
        #    lines.append([0,0,{
        #        'invoice_line_tax_ids': [ imp ],
        #        'product_id': product_id,
        #        'name': 'MontoImpuesto IVATerc' ,
        #        'price_unit': dte['Encabezado']['Totales']['IVATerc'],
        #        'quantity': 1,
        #        'price_subtotal': dte['Encabezado']['Totales']['IVATerc'],
        #        'account_id':  journal_document_class_id.journal_id.default_debit_account_id.id
        #        }]
        #    )
        data['referencias'] = [(5,)]
        for ref in documento.findall("Referencia"):
            data['referencias'].append(self._prepare_ref(ref))
        data["invoice_line_ids"] = lines
        MntNeto = Encabezado.find("Totales/MntNeto")
        mnt_neto = 0
        if MntNeto is not None:
            mnt_neto = int(MntNeto.text or 0)
        MntExe = Encabezado.find("Totales/MntExe")
        if MntExe is not None:
            mnt_neto += int(MntExe.text or 0)
        data["amount_untaxed"] = mnt_neto
        data["amount_total"] = int(Encabezado.find("Totales/MntTotal").text)
        if document_id:
            purchase_to_done = False
            if document_id.purchase_to_done:
                purchase_to_done = document_id.purchase_to_done.ids()
            if purchase_to_done:
                data["purchase_to_done"] = purchase_to_done
        _logger.info('LOG: antes de retornar 770 data {}'.format(data))
        return data

    def _inv_exist(self, documento):
        encabezado = documento.find("Encabezado")
        IdDoc = encabezado.find("IdDoc")
        query = [
            ("sii_document_number", "=", IdDoc.find("Folio").text),
            ("document_class_id.sii_code", "=", IdDoc.find("TipoDTE").text),
        ]
        if self.type == "ventas":
            query.append(("type", "in", ["out_invoice", "out_refund"]))
            Receptor = encabezado.find("Receptor")
            query.append(("partner_id.vat", "=", self.format_rut(Receptor.find("RUTRecep").text)))
        else:
            Emisor = encabezado.find("Emisor")
            query.append(("partner_id.vat", "=", self.format_rut(Emisor.find("RUTEmisor").text)))
            query.append(("type", "in", ["in_invoice", "in_refund"]))
        return self.env["account.invoice"].search(query)

    def _create_inv(self, documento, company_id):
        _logger.info('LOG: se create')
        inv = self._inv_exist(documento)
        if inv:
            return inv
        data = self._get_data(documento, company_id)

        inv = self.env["account.invoice"].create(data)

        _logger.info('LOG: antes de retonrar ultimo punto 797', data)
        return inv

    def _dte_exist(self, documento):
        encabezado = documento.find("Encabezado")
        Emisor = encabezado.find("Emisor")
        IdDoc = encabezado.find("IdDoc")
        new_partner = Emisor.find("RUTEmisor").text
        if Emisor.find("RznSoc") is not None:
            new_partner += " " + Emisor.find("RznSoc").text
        else:
            new_partner += " " + Emisor.find("RznSocEmisor").text
        _logger.info('LOG************* en dte exist')
        return self.env["mail.message.dte.document"].search(
            [
                ("number", "=", IdDoc.find("Folio").text),
                ("document_class_id.sii_code", "=", IdDoc.find("TipoDTE").text),
                "|",
                ("partner_id.vat", "=", self.format_rut(Emisor.find("RUTEmisor").text)),
                ("new_partner", "=", new_partner),
            ]
        )

    def _create_pre(self, documento, company_id):
        dte = self._dte_exist(documento)
        if dte:
            _logger.warning(
                _("El documento {} {} ya se encuentra registrado".format(dte.number, dte.document_class_id.name))
            )
            return dte
        data = self._get_data(documento, company_id, ignore_journal=True)
        data.update(
            {"dte_id": self.dte_id.id,}
        )
        return self.env["mail.message.dte.document"].create(data)

    def _get_dtes(self):
        xml = self._read_xml("etree")
        if xml.tag == "SetDTE":
            return xml.findall("DTE")
        envio = xml.find("SetDTE")
        if envio is None:
            if xml.tag == "DTE":
                return [xml]
            return []
        return envio.findall("DTE")

    def do_create_pre(self):
        created = []
        self.do_receipt_deliver()
        dtes = self._get_dtes()
        for dte in dtes:
            try:
                documento = dte.find("Documento")
                company_id = self.env["res.company"].search(
                    [("vat", "=", self.format_rut(documento.find("Encabezado/Receptor/RUTRecep").text)),], limit=1,
                )
                if not company_id:
                    _logger.warning("No existe compañia para %s" % documento.find("Encabezado/Receptor/RUTRecep").text)
                    continue
                pre = self._create_pre(documento, company_id,)
                if pre:
                    inv = self._inv_exist(documento)
                    pre.write(
                        {"xml": etree.tostring(dte), "invoice_id": inv.id,}
                    )
                    created.append(pre.id)
            except Exception as e:
                _logger.warning("Error en 1 pre con error:  %s" % str(e))
        return created

    def do_create_inv(self):
        created = []
        dtes = self._get_dtes()
        for dte in dtes:
            try:
                company_id = self.document_id.company_id
                documento = dte.find("Documento")
                path_rut = "Encabezado/Receptor/RUTRecep"
                if self.type == "ventas":
                    path_rut = "Encabezado/Emisor/RUTEmisor"
                company_id = self.env["res.company"].search(
                    [("vat", "=", self.format_rut(documento.find(path_rut).text)),], limit=1,
                )
                _logger.info('LOG: punto 1')
                inv = self._create_inv(documento, company_id,)
                _logger.info('LOG: se creo inv', inv)
                if self.document_id:
                    self.document_id.invoice_id = inv.id
                if inv:
                    created.append(inv.id)
                if not inv:
                    raise UserError(
                        "El archivo XML no contiene documentos para alguna empresa registrada en Odoo, o ya ha sido procesado anteriormente "
                    )
                if self.type == "ventas" or self.option == "accept":
                    inv._onchange_partner_id()
                    inv._onchange_invoice_line_ids()
                    inv.action_move_create()
                    guardar = {
                        "document_class_id": inv.document_class_id.id,
                        "sii_document_number": inv.sii_document_number,
                    }
                    if self.type == "ventas":
                        inv.move_id.write(guardar)
                        inv.state = "open"
                if self.type == "compras":
                    inv.set_reference()
                Totales = documento.find("Encabezado/Totales")
                monto_xml = float(Totales.find("MntTotal").text)
                if inv.amount_total == monto_xml:
                    continue
                inv.amount_total = monto_xml
                for t in inv.tax_line_ids:
                    if Totales.find("TasaIVA") is not None and t.tax_id.amount == float(Totales.find("TasaIVA").text):
                        t.amount = float(Totales.find("IVA").text)
                        t.amount_total = float(Totales.find("IVA").text)
                        t.base = float(Totales.find("MntNeto").text)
                    else:
                        t.base = float(Totales.find("MntExe").text)
            except Exception as e:
                _logger.warning("Error en crear 1 factura con error:  %s" % str(e))
        if created and self.option not in [False, "upload"] and self.type == "compras":
            datos = {
                "invoice_ids": [(6, 0, created)],
                "action": "ambas",
                "claim": "ACD",
                "estado_dte": "0",
                "tipo": "account.invoice",
            }
            wiz_accept = self.env["sii.dte.validar.wizard"].create(datos)
            wiz_accept.confirm()
        return created

    def prepare_purchase_line(self, line, document_id, date_planned, company_id, price_included=False, exenta=False):
        product = self._buscar_producto(document_id, line, company_id, price_included, exenta)
        _logger.info('LOGG::. in purchase line')
        if not product:
            return False
        if isinstance(product, int):
            product = self.env["product.product"].browse(product)
        price_subtotal = float(line.find("MontoItem").text)
        discount = 0
        if line.find("DescuentoPct") is not None:
            discount = float(line.find("DescuentoPct").text)
        price = float(line.find("PrcItem").text) if line.find("PrcItem") is not None else price_subtotal
        DscItem = line.find("DscItem")
        values = {
            "name": DscItem.text if DscItem is not None else line.find("NmbItem").text,
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "taxes_id": [(6, 0, product.supplier_taxes_id.ids)],
            "price_unit": price,
            "discount": discount,
            "product_qty": line.find("QtyItem").text if line.find("QtyItem") is not None else 1,
            "date_planned": date_planned,
        }
        return (0, 0, values)

    def _purchase_exist(self, purchase_vals, partner):
        purchase_model = self.env["purchase.order"]
        # antes de crear la OC, verificar que no exista otro documento con los mismos datos
        other_orders = purchase_model.search(
            [
                ("partner_id", "=", purchase_vals["partner_id"]),
                ("partner_ref", "=", purchase_vals["partner_ref"]),
                ("company_id", "=", purchase_vals["company_id"]),
            ]
        )
        if other_orders:
            raise UserError(
                "Ya existe un Pedido de compra con Referencia: %s para el Proveedor: %s.\n"
                "No se puede crear nuevamente, por favor verifique." % (purchase_vals["partner_ref"], partner.name)
            )

    def _prepare_purchase(self, documento, company, partner):
        Encabezado = documento.find("Encabezado")
        IdDoc = Encabezado.find("IdDoc")
        purchase_vals = {
            "partner_ref": IdDoc.find("Folio").text,
            "date_order": IdDoc.find("FchEmis").text,
            "partner_id": partner.id,
            "company_id": company.id,
        }
        return purchase_vals

    def _create_po(self, documento, company):
        purchase_model = self.env["purchase.order"]
        path_rut = "Encabezado/Emisor/RUTEmisor"
        RUT = documento.find(path_rut).text
        Encabezado = documento.find("Encabezado")
        price_included = Encabezado.find("MntBruto")
        partner = self.env["res.partner"].search(
            [("active", "=", True), ("parent_id", "=", False), ("vat", "=", self.format_rut(RUT)),]
        )
        if not partner:
            partner = self._create_partner(Encabezado.find("Emisor"))
        elif not partner.supplier:
            partner.supplier = True
        purchase_vals = self._prepare_purchase(documento, company, partner)
        self._purchase_exist(purchase_vals, partner)
        document_id = self._dte_exist(documento)
        lines = [(5,)]
        exenta = documento.find("Encabezado/IdDoc/TipoDTE").text in ["34", "41"]
        for line in documento.findall("Detalle"):
            new_line = self.prepare_purchase_line(
                line, document_id, purchase_vals["date_order"], company, price_included, exenta
            )
            if new_line:
                lines.append(new_line)
        if not lines:
            _logger.warning(
                "No se pudo crear el Pedido de compra xq no hay lineas, verifique si los productos existen en su sistema"
            )
            return False
        purchase_vals["order_line"] = lines
        po = purchase_model.create(purchase_vals)
        po.button_confirm()
        self.env["account.invoice"].search([("purchase_id", "=", po.id)])
        # inv.sii_document_class_id = dte['Encabezado']['IdDoc']['TipoDTE']
        return po

    def do_create_po(self):
        # self.validate()
        dtes = self._get_dtes()
        for dte in dtes:
            documento = dte.find("Documento")
            path_rut = "Encabezado/Receptor/RUTRecep"
            company = self.env["res.company"].search(
                [("vat", "=", self.format_rut(documento.find(path_rut).text)),], limit=1
            )
            tipo_dte = documento.find("Encabezado/IdDoc/TipoDTE").text
            if tipo_dte in ["34", "33"]:
                self._create_po(documento, company)
            elif tipo_dte in ["56", "61"]:
                self._create_inv(documento, company)

# data = {
#     'account_id': 1284, 
#     'type': 'in_invoice', 
#     'fiscal_position': False, 
#     'origin': 'XML Envío: DTE', 
#     'date_invoice': '2021-07-08', 
#     'partner_id': 1949, 
#     'company_id': 3, 
#     'sii_xml_dte': '<DTE><Documento xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ID="FAV_76483167_TR_000017504"><Encabezado><IdDoc><TipoDTE>33</TipoDTE><Folio>17504</Folio><FchEmis>2021-07-08</FchEmis><FmaPago>2</FmaPago></IdDoc><Emisor><RUTEmisor>76483167-5</RUTEmisor><RznSoc>Kleen Supply</RznSoc><GiroEmis>COMERCIALIZADORA DE INSUMOS INDUSTRIALES Y DE USO DOMESTICO Y OTRAS ACTIVIDADES </GiroEmis><Acteco>519000</Acteco><DirOrigen>CARRETERA GRAL. SAN MARTIN 8000 BOD 23D</DirOrigen><CmnaOrigen>QUILICURA</CmnaOrigen><CiudadOrigen>SANTIAGO</CiudadOrigen></Emisor><Receptor><RUTRecep>76991487-0</RUTRecep><RznSocRecep>SERVICIOS LA INVERNADA SpA\t\t</RznSocRecep><GiroRecep>.</GiroRecep><DirRecep>Valle Hermoso, CaminoSan Miguel , Parcela N&#176; 2</DirRecep><CmnaRecep>PAINE</CmnaRecep><CiudadRecep>.</CiudadRecep></Receptor><Totales><MntNeto>67400</MntNeto><TasaIVA>19</TasaIVA><IVA>12806</IVA><MntTotal>80206</MntTotal></Totales></Encabezado><Detalle><NroLinDet>1</NroLinDet><CdgItem><TpoCodigo>INT1</TpoCodigo><VlrCodigo>CCBYB1001</VlrCodigo></CdgItem><NmbItem>BALDE 8LTS ITALIMPIA AMARILLO 8107</NmbItem><DscItem/><QtyItem>3</QtyItem><PrcItem>6600</PrcItem><MontoItem>19800</MontoItem></Detalle><Detalle><NroLinDet>2</NroLinDet><CdgItem><TpoCodigo>INT1</TpoCodigo><VlrCodigo>CCPAS1014</VlrCodigo></CdgItem><NmbItem>PALETA TIPO REMO LISA 4810</NmbItem><DscItem/><QtyItem>2</QtyItem><PrcItem>23800</PrcItem><MontoItem>47600</MontoItem></Detalle><Referencia><NroLinRef>1</NroLinRef><TpoDocRef>801</TpoDocRef><FolioRef>PO01637</FolioRef><FchRef>2021-07-05</FchRef></Referencia><Referencia><NroLinRef>2</NroLinRef><TpoDocRef>801</TpoDocRef><FolioRef>PO01637</FolioRef><FchRef>2021-07-05</FchRef><RazonRef>.</RazonRef></Referencia><TED version="1.0"><DD><RE>76483167-5</RE><TD>33</TD><F>17504</F><FE>2021-07-08</FE><RR>76991487-0</RR><RSR>SERVICIOS LA INVERNADA SpA\t\t</RSR><MNT>80206</MNT><IT1>BALDE 8LTS ITALIMPIA AMARILLO 8107</IT1><CAF version="1.0"><DA><RE>76483167-5</RE><RS>KLEEN SUPPLY SPA</RS><TD>33</TD><RNG><D>15960</D><H>17559</H></RNG><FA>2021-01-12</FA><RSAPK><M>34aR7rFhThv6Xf4D5hC4QMp2UWHU7F87GONmegu1FlufXB+eFJuvKkLkh+FgFfAjN6GhDeSNJE5cBizQQPPvnQ==</M><E>Aw==</E></RSAPK><IDK>300</IDK></DA><FRMA algoritmo="SHA1withRSA">Ql45FS3Lz9XEq+4bvHy2dyAJhi6W/Zg7598Cq9nSJeDmd59OpQtyq/4mm7mzfCR3j0qXMb4JBduH1X+qrxc+RA==</FRMA></CAF><TSTED>2021-07-08T11:02:00</TSTED></DD><FRMT algoritmo="SHA1withRSA">RTIp9HPLmA2FwNoWlS2+elYdsOxCCix3d4lUEof2F30SQPW3/WcpsFwtuVH7UPmJEqavHYlMFuOp6+/YpAHnEQ==</FRMT></TED><TmstFirma>2021-07-08T11:02:00</TmstFirma></Documento></DTE>', 
#     'sii_barcode': '<TED xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0"><DD><RE>76483167-5</RE><TD>33</TD><F>17504</F><FE>2021-07-08</FE><RR>76991487-0</RR><RSR>SERVICIOS LA INVERNADA SpA\t\t</RSR><MNT>80206</MNT><IT1>BALDE 8LTS ITALIMPIA AMARILLO 8107</IT1><CAF version="1.0"><DA><RE>76483167-5</RE><RS>KLEEN SUPPLY SPA</RS><TD>33</TD><RNG><D>15960</D><H>17559</H></RNG><FA>2021-01-12</FA><RSAPK><M>34aR7rFhThv6Xf4D5hC4QMp2UWHU7F87GONmegu1FlufXB+eFJuvKkLkh+FgFfAjN6GhDeSNJE5cBizQQPPvnQ==</M><E>Aw==</E></RSAPK><IDK>300</IDK></DA><FRMA algoritmo="SHA1withRSA">Ql45FS3Lz9XEq+4bvHy2dyAJhi6W/Zg7598Cq9nSJeDmd59OpQtyq/4mm7mzfCR3j0qXMb4JBduH1X+qrxc+RA==</FRMA></CAF><TSTED>2021-07-08T11:02:00</TSTED></DD><FRMT algoritmo="SHA1withRSA">RTIp9HPLmA2FwNoWlS2+elYdsOxCCix3d4lUEof2F30SQPW3/WcpsFwtuVH7UPmJEqavHYlMFuOp6+/YpAHnEQ==</FRMT></TED>', 
#     'journal_id': 17, 
#     'sii_document_number': '17504', 
#     'document_class_id': 4, 
#     'use_documents': False, 
#     'number': '17504', 
#     'date': '2021-07-08', 
#     'new_partner': '76483167-5 Kleen Supply', 
#     'amount': '80206', 
#     'referencias': [
#         (5,), [0, 0, {
#             'origen': 'PO01637', 
#             'sii_referencia_TpoDocRef': 30, 
#             'sii_referencia_CodRef': None, 
#             'motivo': None, 
#             'fecha_documento': '2021-07-05'}], [0, 0, {
#                 'origen': 'PO01637', 
#                 'sii_referencia_TpoDocRef': 30, 
#                 'sii_referencia_CodRef': None, 
#                 'motivo': '.', 
#                 'fecha_documento': '2021-07-05'}]], 
#     'invoice_line_ids': [(5,), [0, 0, {
#         'product_id': 7102, 'sequence': '1', 
#         'name': None, 
#         'price_unit': 6600.0, 
#         'discount': 0, 
#         'quantity': '3', 
#         'price_subtotal': 19800.0, 
#         'account_id': 4355, 'invoice_line_tax_ids': [(6, 0, [13])], 'uom_id': 1}], [0, 0, {'product_id': 7107, 'sequence': '2', 'name': None, 'price_unit': 23800.0, 'discount': 0, 'quantity': '2', 'price_subtotal': 47600.0, 'account_id': 4355, 'invoice_line_tax_ids': [(6, 0, [13])], 'uom_id': 1}]], 'amount_untaxed': 67400, 'amount_total': 80206}

        

# 2021-11-18 19:41:59,522 5 INFO dimabe-odoo-la-invernada-mtest-fe-3496090 odoo.addons.l10n_cl_fe.wizard.upload_xml: LOG: antes del encabezado
# data ={
#     'account_id': 1284, 
#     'type': 'in_invoice', 
#     'fiscal_position': False, 
#     'origin': 'XML Envío: DTE', 
#     'date_invoice': '2021-07-08', 
#     'partner_id': 1949, 
#     'company_id': 3, 
#     'sii_xml_dte': '<DTE><Documento xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ID="FAV_76483167_TR_000017504"><Encabezado><IdDoc><TipoDTE>33</TipoDTE><Folio>17504</Folio><FchEmis>2021-07-08</FchEmis><FmaPago>2</FmaPago></IdDoc><Emisor><RUTEmisor>76483167-5</RUTEmisor><RznSoc>Kleen Supply</RznSoc><GiroEmis>COMERCIALIZADORA DE INSUMOS INDUSTRIALES Y DE USO DOMESTICO Y OTRAS ACTIVIDADES </GiroEmis><Acteco>519000</Acteco><DirOrigen>CARRETERA GRAL. SAN MARTIN 8000 BOD 23D</DirOrigen><CmnaOrigen>QUILICURA</CmnaOrigen><CiudadOrigen>SANTIAGO</CiudadOrigen></Emisor><Receptor><RUTRecep>76991487-0</RUTRecep><RznSocRecep>SERVICIOS LA INVERNADA SpA\t\t</RznSocRecep><GiroRecep>.</GiroRecep><DirRecep>Valle Hermoso, CaminoSan Miguel , Parcela N&#176; 2</DirRecep><CmnaRecep>PAINE</CmnaRecep><CiudadRecep>.</CiudadRecep></Receptor><Totales><MntNeto>67400</MntNeto><TasaIVA>19</TasaIVA><IVA>12806</IVA><MntTotal>80206</MntTotal></Totales></Encabezado><Detalle><NroLinDet>1</NroLinDet><CdgItem><TpoCodigo>INT1</TpoCodigo><VlrCodigo>CCBYB1001</VlrCodigo></CdgItem><NmbItem>BALDE 8LTS ITALIMPIA AMARILLO 8107</NmbItem><DscItem/><QtyItem>3</QtyItem><PrcItem>6600</PrcItem><MontoItem>19800</MontoItem></Detalle><Detalle><NroLinDet>2</NroLinDet><CdgItem><TpoCodigo>INT1</TpoCodigo><VlrCodigo>CCPAS1014</VlrCodigo></CdgItem><NmbItem>PALETA TIPO REMO LISA 4810</NmbItem><DscItem/><QtyItem>2</QtyItem><PrcItem>23800</PrcItem><MontoItem>47600</MontoItem></Detalle><Referencia><NroLinRef>1</NroLinRef><TpoDocRef>801</TpoDocRef><FolioRef>PO01637</FolioRef><FchRef>2021-07-05</FchRef></Referencia><Referencia><NroLinRef>2</NroLinRef><TpoDocRef>801</TpoDocRef><FolioRef>PO01637</FolioRef><FchRef>2021-07-05</FchRef><RazonRef>.</RazonRef></Referencia><TED version="1.0"><DD><RE>76483167-5</RE><TD>33</TD><F>17504</F><FE>2021-07-08</FE><RR>76991487-0</RR><RSR>SERVICIOS LA INVERNADA SpA\t\t</RSR><MNT>80206</MNT><IT1>BALDE 8LTS ITALIMPIA AMARILLO 8107</IT1><CAF version="1.0"><DA><RE>76483167-5</RE><RS>KLEEN SUPPLY SPA</RS><TD>33</TD><RNG><D>15960</D><H>17559</H></RNG><FA>2021-01-12</FA><RSAPK><M>34aR7rFhThv6Xf4D5hC4QMp2UWHU7F87GONmegu1FlufXB+eFJuvKkLkh+FgFfAjN6GhDeSNJE5cBizQQPPvnQ==</M><E>Aw==</E></RSAPK><IDK>300</IDK></DA><FRMA algoritmo="SHA1withRSA">Ql45FS3Lz9XEq+4bvHy2dyAJhi6W/Zg7598Cq9nSJeDmd59OpQtyq/4mm7mzfCR3j0qXMb4JBduH1X+qrxc+RA==</FRMA></CAF><TSTED>2021-07-08T11:02:00</TSTED></DD><FRMT algoritmo="SHA1withRSA">RTIp9HPLmA2FwNoWlS2+elYdsOxCCix3d4lUEof2F30SQPW3/WcpsFwtuVH7UPmJEqavHYlMFuOp6+/YpAHnEQ==</FRMT></TED><TmstFirma>2021-07-08T11:02:00</TmstFirma></Documento></DTE>', 'sii_barcode': '<TED xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0"><DD><RE>76483167-5</RE><TD>33</TD><F>17504</F><FE>2021-07-08</FE><RR>76991487-0</RR><RSR>SERVICIOS LA INVERNADA SpA\t\t</RSR><MNT>80206</MNT><IT1>BALDE 8LTS ITALIMPIA AMARILLO 8107</IT1><CAF version="1.0"><DA><RE>76483167-5</RE><RS>KLEEN SUPPLY SPA</RS><TD>33</TD><RNG><D>15960</D><H>17559</H></RNG><FA>2021-01-12</FA><RSAPK><M>34aR7rFhThv6Xf4D5hC4QMp2UWHU7F87GONmegu1FlufXB+eFJuvKkLkh+FgFfAjN6GhDeSNJE5cBizQQPPvnQ==</M><E>Aw==</E></RSAPK><IDK>300</IDK></DA><FRMA algoritmo="SHA1withRSA">Ql45FS3Lz9XEq+4bvHy2dyAJhi6W/Zg7598Cq9nSJeDmd59OpQtyq/4mm7mzfCR3j0qXMb4JBduH1X+qrxc+RA==</FRMA></CAF><TSTED>2021-07-08T11:02:00</TSTED></DD><FRMT algoritmo="SHA1withRSA">RTIp9HPLmA2FwNoWlS2+elYdsOxCCix3d4lUEof2F30SQPW3/WcpsFwtuVH7UPmJEqavHYlMFuOp6+/YpAHnEQ==</FRMT></TED>', 
#     'journal_id': 17, 'sii_document_number': 
#     '17504', 'document_class_id': 4, 
#     'use_documents': False, 
#     'number': '17504', 
#     'date': 
#     '2021-07-08', 
#     'new_partner': '76483167-5 Kleen Supply', 
#     'amount': '80206', 
#     'referencias': [(5,), [0, 0, {'origen': 'PO01637', 'sii_referencia_TpoDocRef': 30, 'sii_referencia_CodRef': None, 'motivo': None, 'fecha_documento': '2021-07-05'}], [0, 0, {'origen': 'PO01637', 'sii_referencia_TpoDocRef': 30, 'sii_referencia_CodRef': None, 'motivo': '.', 'fecha_documento': '2021-07-05'}]], 
#     'invoice_line_ids': [(5,), [0, 0, 
#     {'product_id': 7102, 
#     'sequence': '1', 
#     'name': None, 
#     'price_unit': 6600.0, 
#     'discount': 0, 
#     'quantity': '3', 
#     'price_subtotal': 19800.0, 
#     'account_id': 4355, 'invoice_line_tax_ids': [(6, 0, [13])], 'uom_id': 1}], [0, 0, {'product_id': 7107, 'sequence': '2', 'name': None, 'price_unit': 23800.0, 'discount': 0, 'quantity': '2', 'price_subtotal': 47600.0, 'account_id': 4355, 'invoice_line_tax_ids': [(6, 0, [13])], 'uom_id': 1}]], 'amount_untaxed': 67400, 'amount_total': 80206}

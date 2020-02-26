odoo.define('dimabe_manufacturing.validate_on_scanned', function (require) {
    'use strict';
    let core = require('web.core');
    let model = require('web.Model');
    let formViewBarcodeHandler = require('barcodes.FormViewBarcodeHandler');
    let _t = core._t;
    let validateOnScanned = formViewBarcodeHandler.extend({
        init: function (parent, context) {
            alert(_t('init'))
        },
        start: function () {
            alert(_t('start'))
        },
        pre_onchange_hook: function (barcode) {
            alert(_t('pre_onchange_hook'))
        },
        open_wizard: function (action) {
            alert(_t('open_wizard'))
        }
    });

    return validateOnScanned;
});


odoo.define('stock_production_lot.stock_report_button', function (require) {
    "use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var _t = core._t;
    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.find('#generate_report_xml').click(this.proxy('action_def'));
            }
        },
        action_def: function () {
            console.log('Prueba')
            var self = this
            var user = session.uid;
            rpc.query({
                model: 'stock.production.lot',
                method: 'generate_excel_raw_report',
                args: [[user], {'id': user}],
            }).then(function (e) {
            });
        }
    });
}
)

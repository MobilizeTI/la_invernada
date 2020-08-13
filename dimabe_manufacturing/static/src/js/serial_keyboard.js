odoo.define('serial_keyboard.confirmed', function (require) {
        "use strict";
        var core = require('web.core');
        var ListController = require('web.ListController');
        var rpc = require('web.rpc');
        var session = require('web.session');
        var _t = core._t;
        ListController.include({
            renderButtons: function ($node) {
                this._super.apply(this, arguments);
                let barcode = $('#confirmed_serial').click(this.proxy('action_data'));
            },
            action_data: function () {
                var self = this
                let barcode = $('#confirmed_serial').val();
                console.log(barcode)
                var user = session.uid;
                rpc.query({
                    model: 'mrp.workorder',
                    method: 'on_barcode_scanned',
                    args: [[user], {'id': user}, {'barcode': '10120146022'}],
                }).then(function (e) {
                });

            }
        });
    }
)
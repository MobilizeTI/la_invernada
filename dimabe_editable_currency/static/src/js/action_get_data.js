odoo.define('balance_sheet_clp.get_data', function (require) {
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
                    this.$buttons.find('#usd_update').click(this.proxy('action_data'));
                }
            },
            action_data: function () {
                var self = this
                var user = session.uid;
                rpc.query({
                    model: 'balance.sheet.clp',
                    method: 'get_balance_clp',
                    args: [[user], {'id': user}],
                }).then(function (e) {
                    self.do_action('dimabe_editable_currency.action_balance_sheet_clp_views');
                });

            }
        });
    }
)
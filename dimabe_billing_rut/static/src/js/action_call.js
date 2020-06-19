odoo.define('custom_invoice.sincronize_button', function (require) {
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
                this.$buttons.find('.oe_action_button').click(this.proxy('action_def'));
            }
        },
        action_def: function () {
            var self = this
            var user = session.uid;
            rpc.query({
                model: 'custom.invoice',
                method: 'get_dte',
                args: [[user], {'id': user}],
            });
            window.location();
        }
    });
}
)

odoo.define('balance_sheet_clp.get_data', function (require) {
    "use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var _t = core._t;
    var model_obj = new instance.web.Model('ir.model.data');
    var view_id = false;
    model_obj.call('get_object_reference',['balance.sheet.clp','balance_sheet_clp_view_tree']).then( function(result){
    view_id = result[1];
    });
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
                model: 'balance.sheet.clp',
                method: 'get_data',
                args: [[user], {'id': user}],

            });
        }
    });
}
)

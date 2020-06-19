odoo.define('dimabe_billing_rut.sincronize_now', function (require) {
        "use string"
        var core = require('web.core');
        var ListController = require('web.ListController');
        var rpc = require('web.rpc')
        var session = require('web.session');
        var _t = core._t;
        ListController.include({
            renderButtons : function ($node) {
                this._super.apply(this,arguments);
                if(this.$buttons){
                    this.$buttons.find('.oe_action_button').click(this.proxy('action_def'))
                }
            },
            action_def: function () {
            var self =this
            var user = session.uid;
            rpc.query({
                model: 'custom.invoce',
                method: 'get_dte',
                args: [[user],{'id':user}],
                });
            },
        })
    }
)

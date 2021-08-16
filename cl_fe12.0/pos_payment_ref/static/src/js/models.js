odoo.define('pos_payment_ref.models', function (require) {
"use strict";

var models = require('point_of_sale.models');

models.load_fields("account.journal", "pos_payment_ref");


var paymentline_super = models.Paymentline.prototype;
models.Paymentline = models.Paymentline.extend({
	initialize: function(attr, options){
		this.payment_ref = "";
		var res = paymentline_super.initialize.call(this, attr, options);
		return res;
	},
	init_from_JSON: function (json) {
        paymentline_super.init_from_JSON.apply(this, arguments);

        this.payment_ref = json.payment_ref;
    },
    export_as_JSON: function () {
        return _.extend(paymentline_super.export_as_JSON.apply(this, arguments), {
            payment_ref: this.payment_ref,
        });
    },
    set_voucher_number: function (payment_ref) {
		this.payment_ref = payment_ref;
		this.trigger('change',this);
	},
	get_voucher_number: function () {
		return this.payment_ref || "";
	}
});

return models;
});
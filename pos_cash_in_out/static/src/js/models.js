odoo.define('pos_cash_in_out.models', function (require) {
	"use strict";

	var models = require('point_of_sale.models');
	
	var _super_Order = models.Order.prototype;
	models.Order = models.Order.extend({
        set_cash_in_out_details: function(cash_in_out_details){
            this.cash_in_out_details = cash_in_out_details;
        },
        get_cash_in_out_details: function(){
            return this.cash_in_out_details;
        },
    });

});
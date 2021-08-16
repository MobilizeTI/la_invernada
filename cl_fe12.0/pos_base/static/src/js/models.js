odoo.define('pos_base.models', function (require) {
	"use strict";
    
	var models = require('point_of_sale.models');

	var _super_Order = models.Order.prototype;
	
	models.load_fields("account.journal", ['use_in_pos_for']);
	models.load_fields("product.product", ['is_dummy_product']);
	
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_Order.initialize.apply(this, arguments);
            var self = this;
            this.orderlines.bind('change add remove', function (line) {
                self.pos.trigger('update:count_item')
            });
        },
        empty_cart: function(){
        	var self = this;
        	var line;
        	while (self.get_orderlines().length) {
        		line = self.get_orderlines()[0];
        		self.remove_orderline(line);
        	}
        	while (self.get_paymentlines().length) {
                line = self.get_paymentlines()[0];
                self.remove_paymentline(line);
            }
	    },
    });

});

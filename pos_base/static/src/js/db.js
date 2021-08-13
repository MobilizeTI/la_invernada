odoo.define('pos_base.DB', function (require) {
"use strict";

var DB = require('point_of_sale.DB');

DB.include({
	init: function(options){
        this._super.apply(this, arguments);
        this.dummy_product_ids = [];
	},
	get_dummy_product_ids: function(){
    	return this.dummy_product_ids;
    },
	add_products: function(products){
        var new_write_date = '';
        var product;
        for(var i = 0, len = products.length; i < len; i++){
            product = products[i];
            if(product.is_dummy_product){
            	this.dummy_product_ids.push(product.id);
            }
        }
        this._super(products);
    },
});

});

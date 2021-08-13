odoo.define('stock_transfers_pos.models', function (require) {
"use strict";

var utils = require('web.utils');

var models = require('point_of_sale.models');
var models_stock = require('pos_stock_quantity.pos_stock').models;


var PosModelSuper = models_stock.PosModel.prototype;
var PosOrderSuper = models.Order.prototype;

models.PosModel = models.PosModel.extend({
    is_allow_out_of_stock: function(){
		var order = this.get_order();
		// cuando sea NC, no deshabilitar productos sin stock
		if (order && order.GetSaleMode() === "internal_transfer_receive"){
			return true;
		}
		return PosModelSuper.is_allow_out_of_stock.call(this);
	}
});

models.Order = models.Order.extend({
	initialize: function(attributes, options){
		this.SaleMode = "";
		var res = PosOrderSuper.initialize.call(this, attributes, options);
		return res;
	},
	export_as_JSON: function() {
        var data = PosOrderSuper.export_as_JSON.apply(this, arguments);
        data.SaleMode = this.SaleMode;
        return data;
    },
    init_from_JSON: function(json) {
        this.SaleMode = json.SaleMode;
        PosOrderSuper.init_from_JSON.call(this, json);
    },
	SetSaleMode: function(NewSaleMode) {
        this.SaleMode = NewSaleMode;
    },
    GetSaleMode: function() {
        return this.SaleMode || "";
    }
});

});

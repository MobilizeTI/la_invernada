odoo.define('pos_pricelist.models', function (require) {
"use strict";

var utils = require('web.utils');

var models = require('point_of_sale.models');

var round_pr = utils.round_precision;
var OrderlineSuper = models.Orderline.prototype;

models.load_fields("product.pricelist", ["discount_policy"]);

models.Order = models.Order.extend({
	get_total_discount: function() {
        return round_pr(this.orderlines.reduce((function(sum, orderLine) {
            return sum + (orderLine.get_discount_value() * orderLine.get_quantity());
        }), 0), this.pos.currency.rounding);
    }
});

models.Orderline = models.Orderline.extend({
	initialize: function(attr, options){
		this.discount_value = 0;
		var res = OrderlineSuper.initialize.call(this, attr, options);
		if(this.product && attr.product_list_price){
			this.product_list_price = attr.product_list_price; 
		}
		return res;
	},
	get_product_list_price: function(){
		return this.product_list_price || this.get_product().lst_price;
	},
	get_discount_value: function(){
		return this.discount_value;
	},
	set_discount: function(discount, skip_calculate_discount){
		// calcular el valor del descuento antes de la llamada super
		// xq al hacerlo despues no se refrescan bien los datos
		if (!skip_calculate_discount){
			var disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
			var discount_value = 0.0
			if (disc > 0){
				discount_value = this.get_unit_price() * disc * 0.01;
			}
			this.discount_value = discount_value;
		}
		var res = OrderlineSuper.set_discount.call(this, discount);
		return res;
	},
	get_base_price: function(){
		if (this.get_discount_value() > 0){
			var rounding = this.pos.currency.rounding;
			return round_pr(((this.get_unit_price() * this.get_quantity()) - (this.get_discount_value() * this.get_quantity())), rounding);
		} else {
			return OrderlineSuper.get_base_price.call(this);
		}
    },
	get_price_reduce: function(){
		if (this.get_discount_value() > 0){
			return this.get_unit_price() - this.get_discount_value();
		} else {
			return OrderlineSuper.get_price_reduce.call(this);
		}
    },
	set_unit_price: function(price){
		var self = this;
		// cuando en la lista de precios esta configurado que se muestre el descuento
		// pasar siempre el precio de venta del producto y solo calcular el descuento
		if (self.order.pricelist.discount_policy === 'without_discount'){			
			var lst_price = this.get_product_list_price();
			if (lst_price != 0){
				var discount_value = 0.0
				var discount = Math.round(((lst_price - price) / lst_price * 100), 2);
				if (discount > 0 & discount <= 100){
					if (lst_price > price){
						discount_value = lst_price - price;
					}
					this.discount_value = discount_value;
					price = lst_price;
					this.set_discount(discount, true);
				}else{
					this.set_discount(0);
					this.discount_value = discount_value;
				}
			}
		}
		return OrderlineSuper.set_unit_price.call(this, price);
	},
	can_be_merged_with: function(orderline){
		var self = this;
		var can_be_merge = OrderlineSuper.can_be_merged_with.call(this, orderline);
		if (self.order.pricelist.discount_policy === 'without_discount'){
			// cuando no se puede hacer merge pero es xq tiene descuento > 0
			// verificar si el descuento es el mismo de la nueva linea y permitir hacer merge
			if(!can_be_merge & this.get_product().id === orderline.get_product().id & self.get_discount() > 0){
				if(self.get_discount() === orderline.get_discount()){
					can_be_merge = true;
				}
			}
		}
		return can_be_merge;
	},
	init_from_JSON: function(json) {
		var res = OrderlineSuper.init_from_JSON.call(this, json);
		// despues de cargar desde el JSon
		// volver a calcular el descuento 
		// xq el discount_value no estaba establecido aun 
		if (json.discount_value && json.discount){
			this.discount_value = json.discount_value;
			this.set_discount(json.discount, true);
		}
		return res;
	},
	export_as_JSON: function() {
		var res = OrderlineSuper.export_as_JSON.call(this);
		res.discount_value = this.discount_value;
		return res
	},
	export_for_printing: function(){
		var self = this;
		var values_printing = OrderlineSuper.export_for_printing.call(this);
		if (self.order.pricelist.discount_policy === 'without_discount'){
			values_printing.price = self.get_product().lst_price;
			values_printing.discount_value = self.discount_value;
		}
		return values_printing;
	}
});

});

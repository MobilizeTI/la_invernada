odoo.define('pos_cash_in_out.screens', function(require) {
	"use strict";
	
	var core = require('web.core');
	var QWeb = core.qweb;
	var _t = core._t;

	var screens = require('point_of_sale.screens');
	
	screens.ReceiptScreenWidget.include({
		get_receipt_render_env: function() {
			var order = this.pos.get_order();
			var receipt_env = this._super();
			receipt_env.money_data = order.get_cash_in_out_details();
			return receipt_env;
		},
        get_xml_template_to_print: function(order) {
        	if(order.get_cash_in_out_details()){
        		return "XmlCashInOutTicket";
        	} else {
        		return this._super(order);
        	}
    	},
    	get_pdf_template_to_print: function(order) {
        	if(order.get_cash_in_out_details()){
        		return "CashInOutTicket";
        	} else {
        		return this._super(order);
        	}
    	}
    });

	var ButtonCashIn = screens.ActionButtonWidget.extend({
		template : 'button_cash_in',
		button_click : function() {
			var self = this
			self.gui.show_popup('cash_in_out_popup', {
		    	button: this,
		    	title: "Ingresar Dinero a Caja",
		    	msg: 'Por favor ingrese el motivo y el monto a ingresar',
		    	operation: "put_money",
		    });
		}
	});

	var ButtonCashOut = screens.ActionButtonWidget.extend({
		template : 'button_cash_out',
		button_click : function() {
			var self = this
			self.gui.show_popup('cash_in_out_popup', {
		    	button: this,
		    	title: "Sacar Dinero de Caja",
		    	msg: 'Por favor ingrese el motivo y el monto a sacar',
		    	operation: "take_money",
		    });
		}
	});

	screens.define_action_button({
		'name' : 'button_cash_in',
		'widget' : ButtonCashIn,
		'condition' : function() {
			return this.pos.config.enable_cash_in_out == true;
		}
	});

	screens.define_action_button({
		'name' : 'button_cash_out',
		'widget' : ButtonCashOut,
		'condition' : function() {
			return this.pos.config.enable_cash_in_out == true;
		}
	});

	return {
		ButtonCashIn : ButtonCashIn,
		ButtonCashOut : ButtonCashOut,
	};
});
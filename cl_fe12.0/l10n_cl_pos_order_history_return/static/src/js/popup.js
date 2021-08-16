odoo.define('l10n_cl_pos_order_history_return.popup', function (require) {
	"use strict";
	
	var gui = require('point_of_sale.gui');
	var rpc = require('web.rpc');
	var core = require('web.core');
	var PopupWidget = require('point_of_sale.popups');
	var models = require('point_of_sale.models');
	
	var _t = core._t;

    var OrderReturnPopup = PopupWidget.extend({
        template: 'OrderReturnPopup',
        init: function(parent, args) {
	    	var self = this;
	        this._super(parent, args);
	        this.options = {};
	        this.pos_return_data = {};
	    },
	    show: function(options){
	    	var self = this;
	        options = options || {};
	        this.pos_return_data = {};
	        this.filter_refund = options.filter_refund ? parseInt(options.filter_refund) : undefined;
	        this.note_id = options.note_id ? parseInt(options.note_id) : undefined;
	        this._super(options);
	    },
	    get_filter_refund: function(){
	    	return this.filter_refund;
	    },
	    get_note: function(){
	    	return this.note_id;
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var selectedOrder = this.pos.get_order();
    		var close_popup = false;
    		var has_returns = false;
    		var fields_warnings = self.validate_fields_aditional();
            if (fields_warnings.length > 0){
            	return;
            }
        	var return_data_aditional = self.get_fields_aditional();
        	var msj_order = selectedOrder.set_fields_for_return(return_data_aditional);
        	if (msj_order){
        		return self.chrome.pos_warning("Devolucion de Productos", msj_order);
    		} else{
    			close_popup = true;
    		}
        	if(close_popup){
            	this.gui.close_popup();
            	return;
            }
	    }
    });
    
    gui.define_popup({name:'order_return_popup', widget: OrderReturnPopup});
    
    return {
    	OrderReturnPopup: OrderReturnPopup,
    };

});
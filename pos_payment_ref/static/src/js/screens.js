odoo.define('pos_payment_ref.screens', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var BarcodeEvents = require('barcodes.BarcodeEvents').BarcodeEvents;

screens.PaymentScreenWidget.include({
	init: function(parent, options) {
		var self = this;
        this._super(parent, options);
        var keyboard_handler_super = this.keyboard_handler;
        this.keyboard_handler = function(event){
        	if (event.target.id == "voucher_number"){
        		// On mobile Chrome BarcodeEvents relies on an invisible
                // input being filled by a barcode device. Let events go
                // through when this input is focused.
                if (BarcodeEvents.$barcodeInput && BarcodeEvents.$barcodeInput.is(":focus")) {
                    return;
                }

                var key = '';

                if (event.type === "keypress") {
                    if (event.keyCode === 13) { // Enter
                        self.validate_order();
                    } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
                        key = '' + (event.keyCode - 48);
                        var textbox = document.getElementById("voucher_number");
                        if (textbox.value.length >= 10){
                        	key = '';
                        }
                    }
                } else { // keyup/keydown
                    if (event.keyCode === 46) { // Delete
                        key = 'CLEAR';
                    } else if (event.keyCode === 8) { // Backspace
                        key = 'BACKSPACE';
                    }
                }
	            self.payment_input_voucher_number(key);
	            var textbox = document.getElementById("voucher_number");
	            textbox.focus();
	            textbox.setSelectionRange(textbox.value.length, textbox.value.length);
        	}else{
        		keyboard_handler_super(event)
        	}
            event.preventDefault();
        };
        this.pos.get('orders').bind('add remove change', function () {
			this.renderElement();
		}, this);
	},
	payment_input_voucher_number: function(input) {
        // popup block inputs to prevent sneak editing. 
        if (this.gui.has_popup()) {
            return;
        }
        var order = this.pos.get_order();
        if (order.selected_paymentline) {
        	var voucher_number = order.selected_paymentline.get_voucher_number();
        	if (input === 'BACKSPACE') { 
        		voucher_number = voucher_number.substring(0,voucher_number.length - 1);
            }
        	else if (input === 'CLEAR') { 
        		voucher_number = voucher_number.substring(1,voucher_number.length);	
        	}
        	else{
        		voucher_number += input;	
        	}
            order.selected_paymentline.set_voucher_number(voucher_number);
            this.order_changes();
            this.render_paymentlines();
        }
    },
    validate_order: function(options) {
        var currentOrder = this.pos.get_order();
        var clients = currentOrder.get_client();
        var plines = currentOrder.get_paymentlines();
        for (var i = 0; i < plines.length; i++) {
    		if (plines[i].cashregister.journal.pos_payment_ref) {
    			if (!plines[i].get_voucher_number()){
                    this.gui.show_popup('error',{
                        'title': 'Codigo de autorizacion',
                        'body': 'Debe ingresar el Codigo de autorizacion en la forma de pago ' + plines[i].cashregister.journal_id[1] +'. Por favor verifique',
                    });
                    return;
                }
    		}
        }
        this._super(options);
	},

});

});

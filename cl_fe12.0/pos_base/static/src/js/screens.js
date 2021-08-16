odoo.define('pos_base.screens', function (require) {
"use strict";
var screens = require('point_of_sale.screens');
var core = require('web.core');
var QWeb = core.qweb;

screens.ProductScreenWidget.include({
    start: function () {
        this._super();
        if (this.pos.is_mobile){
        	return;
        }
        var action_buttons = this.action_buttons;
        for (var key in action_buttons) {
            action_buttons[key].appendTo(this.$('.button-list'));
        }
        $('.control-buttons').addClass('oe_hidden');
    }
});

screens.ReceiptScreenWidget.include({
	get_xml_template_to_print: function(order) {
		return false;
	},
	get_pdf_template_to_print: function(order) {
		return false;
	},
	render_receipt: function() {
		var order = this.pos.get_order();
		var templateName = this.get_pdf_template_to_print(order);
        if (templateName) {
            this.$('.pos-receipt-container').html(QWeb.render(templateName, this.get_receipt_render_env()));
        }else{
        	this._super();
        }
    },
    render_xml_receipt: function() {
    	var order = this.pos.get_order();
		var templateName = this.get_xml_template_to_print(order) || 'XmlReceipt';
    	var receipt = QWeb.render(templateName, this.get_receipt_render_env());
    	return receipt;
    },
	print_xml: function() {
    	var receipt = this.render_xml_receipt();

        this.pos.proxy.print_receipt(receipt);
        this.pos.get_order()._printed = true;
    }
});

screens.ActionpadWidget.include({
    renderElement: function() {
        var self = this;
        this._super();
        this.$('.pay').unbind();
        this.$('.pay').click(function () {
            self.action_show_payment_screen();
        });
        this.$('.set-customer').click(function(){
            self.gui.show_screen('clientlist');
        });
    },
    action_show_payment_screen: function() {
    	return this.payment();
    },
    payment: function () {
        // This method has been added to encapsulate the original widget's logic
        // just to make code more clean and readable
        var self = this;
        var order = self.pos.get_order();
            var has_valid_product_lot = _.every(order.orderlines.models, function(line){
                return line.has_valid_product_lot();
            });
            if (has_valid_product_lot) {
                self.gui.show_screen('payment');
            }else{
                self.gui.show_popup('confirm',{
                    'title': _t('Empty Serial/Lot Number'),
                    'body':  _t('One or more product(s) required serial/lot number.'),
                    confirm: function(){
                        self.gui.show_screen('payment');
                    },
                });
            }
    },
});

screens.OrderWidget.include({
	action_refresh_order_buttons : function(buttons, selected_order) {
		return true;
	},
	update_summary : function() {
		this._super();
		var selected_order = this.pos.get_order();
		var buttons = this.getParent().action_buttons;
		if (selected_order && buttons) {
			this.action_refresh_order_buttons(buttons, selected_order);
		}
	}
});

screens.ProductListWidget.include({
	set_product_list: function(product_list){
		var self = this;
		var new_product_list = [];
		var dummy_product_ids = self.pos.db.get_dummy_product_ids();
		if(product_list.length > 0){
			product_list.map(function(product){
				if(($.inArray(product.id, dummy_product_ids) == -1) && (!product.is_dummy_product)){
					new_product_list.push(product);
				}
			});
		}
        this.product_list = new_product_list;
        this.renderElement();
    },
});

screens.set_pricelist_button.include({
	button_click: function () {
		var self = this;
		var _super_bind = self._super.bind(self);
		if (self.pos.config.pin_pricelist.length > 0){
			self.gui.ask_password(self.pos.config.pin_pricelist).then(function(){
				return _super_bind();
	    	});
		}else{
			return self._super();
		}
		
	}
});

});

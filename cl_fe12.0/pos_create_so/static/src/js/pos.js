odoo.define('pos_create_so.pos_create_so', function (require) {
"use strict";

	var screens = require('point_of_sale.screens');
	var rpc = require('web.rpc');
	var core = require('web.core');
	var models = require('point_of_sale.models');
	var PopupWidget    = require('point_of_sale.popups');
	var gui = require('point_of_sale.gui');
	var _t = core._t;
	
	var module_class = {};
	var ValidateClient = function(pos, client) {
		if (!client.name){
			pos.gui.show_popup('error',{
				'title': 'Datos de Cliente Incompletos',
				'body':  'El Cliente seleccionado no tiene Nombre, por favor verifique',
			});
			return false;
		}
		if (!client.street){
			pos.gui.show_popup('error',{
				'title': 'Datos de Cliente Incompletos',
				'body':  'El Cliente seleccionado no tiene la direccion, por favor verifique',
			});
			return false;
		}
		return true;
	};
	
	module_class.ValidateClient = ValidateClient;

	var SaleOrderPopupWidget = PopupWidget.extend({
	    template: 'SaleOrderPopupWidget',
	});
	gui.define_popup({name:'saleOrder', widget: SaleOrderPopupWidget});
	
	var SaleOrderButton = screens.ActionButtonWidget.extend({
	    template: 'SaleOrderButton',
	    button_click: function(){
	        var self = this;
	        var order = this.pos.get_order();
	        var customer = order.get_client();
	        var currentOrderLines = order.get_orderlines();
	        if(currentOrderLines.length <= 0){
	            alert(_t('No product selected!'));
	        } else if(customer == null) {
	        	self.gui.show_popup('confirm',{
                    'title': _t('Please select the Customer'),
                    'body': _t('You need to select the customer before you can invoice an order.'),
                    confirm: function(){
                        self.gui.show_screen('clientlist');
                    },
                });
	        } else {
	        	if (!module_class.ValidateClient(self.pos, customer)){
            		return false;
            	}else{
            		self.gui.show_popup('confirm', {
                        title: 'Esta seguro de crear un Pedido de venta en lugar del Pedido del Pos?',
                        body: 'Si esta seguro, de clic en el boton Confirmar, caso contrario en el boton Cancelar',
                        confirm: function(){
                        	self.pos.create_sale_order();
                        }
                	});	
            	}
	        }
	    },
	});
	
	screens.define_action_button({
	    'name': 'saleorder',
	    'widget': SaleOrderButton,
	    'condition': function(){
	        return this.pos.config.sale_order_operations == "draft" || this.pos.config.sale_order_operations == "confirm";
	    },
	});
	
	screens.PaymentScreenWidget.include({
		events: _.extend({}, screens.PaymentScreenWidget.prototype.events, {
			'click #btn_so': 'click_create_so',
		}),
		click_create_so: function(){
			var self = this;
			var order = self.pos.get_order();
			if(order){
    	        var currentOrderLines = order.get_orderlines();
                var paymentline_ids = [];
                if(order.get_paymentlines().length > 0){
                	var customer = order.get_client();
                    if(currentOrderLines.length <= 0){
                    	alert(_t('No product selected!'));
                    } else if(customer == null) {
                    	self.gui.show_popup('confirm',{
                            'title': _t('Please select the Customer'),
                            'body': _t('You need to select the customer before you can invoice an order.'),
                            confirm: function(){
                                self.gui.show_screen('clientlist');
                            },
                        });
                    } else {
                    	if (!module_class.ValidateClient(self.pos, customer)){
                    		return false;
                    	}else{
                    		self.gui.show_popup('confirm', {
                                title: 'Esta seguro de crear un Pedido de venta/Factura en lugar del Pedido del Pos?',
                                body: 'Si esta seguro, de clic en el boton Confirmar, caso contrario en el boton Cancelar',
                                confirm: function(){
                                	$('#btn_so').hide();
                                	self.pos.create_sale_order();
                                }
                        	});	
                    	}
                    }
                }
			}
		},
		order_changes: function(){
	        var self = this;
	        var res = this._super();
	        var order = this.pos.get_order();
	        if (!order) {
	            return res;
	        } else if (order.is_paid()) {
	            self.$('#btn_so').addClass('highlight');
	        }else{
	            self.$('#btn_so').removeClass('highlight');
	        }
	        return res;
	    },
	});

	var _super_Order = models.Order.prototype;
	models.Order = models.Order.extend({
		set_sale_order_name: function(name){
			this.set('sale_order_name', name);
		},
		get_sale_order_name: function(){
			return this.get('sale_order_name');
		},
		export_for_printing: function(){
            var orders = _super_Order.export_for_printing.call(this);
            var new_val = {
            	sale_order_name: this.get_sale_order_name() || false,
            };
            $.extend(orders, new_val);
            return orders;
        },
	});
	var _super_posmodel = models.PosModel;
	models.PosModel = models.PosModel.extend({
		create_sale_order: function(){
            var self = this;
            var order = this.get_order();
	        var currentOrderLines = order.get_orderlines();
	        var customer_id = order.get_client().id;
	        var paymentlines = false;
	        var paid = false;
	        var confirm = false;
            var orderLines = [];
            for(var i=0; i<currentOrderLines.length;i++){
                orderLines.push(currentOrderLines[i].export_as_JSON());
            }
            if(self.config.sale_order_operations === "paid") {
                paymentlines = [];
                _.each(order.get_paymentlines(), function(paymentline){
                    paymentlines.push({
                        'journal_id': paymentline.cashregister.journal_id[0],
                        'amount': paymentline.get_amount(),
                        'statement_id': paymentline.cashregister.id,
                    })
                });
                paid = true
            }
            if(self.config.sale_order_operations === "confirm"){
                confirm = true;
            }
            var params = {
            	model: 'sale.order',
            	method: 'create_sales_order',
            	args: [orderLines, customer_id, self.config.id, paymentlines],
            	context: {'confirm': confirm, 'paid': paid}
            }
            rpc.query(params, {async: false})
            	.then(function(sale_order){
	                if(sale_order){
	                    if(paid){
	                        $('#btn_so').show();
	                        order.finalize();
	                        if (sale_order.invoice_id && sale_order.invoice_name){
	                        	var url = window.location.origin + '/web#id=' + sale_order.invoice_id + '&view_type=form&model=account.invoice';
		                        self.gui.show_popup('saleOrder', {'url': url, 'name': sale_order.invoice_name});
		                        self.chrome.do_action('account.account_invoices', {additional_context:{
		                            active_ids: [sale_order.invoice_id],
		                        }});
	                        }else{
	                        	self.gui.show_screen('products');
	                        }
	                    } else{
	                        order.finalize();
	                        var url = window.location.origin + '/web#id=' + sale_order.id + '&view_type=form&model=sale.order';
	                        self.gui.show_popup('saleOrder', {'url': url, 'name': sale_order.name});
	                    }
	                }
	            }).fail(function(error_type, error){
	                if(paid){
	                    $('#btn_so').show();
	                }
	                if (error.code === 200) { // Odoo Errors
	                    self.gui.show_popup('error-traceback',{
	                        'title': error.data.message || _t("Server Error"),
	                        'body': error.data.debug || _t('The server encountered an error while receiving your order.'),
	                    });
	                } else {                            // ???
	                    self.gui.show_popup('error',{
	                        'title': _t("Unknown Error"),
	                        'body':  _t("The order could not be sent to the server due to an unknown error"),
	                    });
	                }
	            });
        },
	});
	
	return module_class;
});


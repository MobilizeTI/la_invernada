odoo.define('pos_cash_in_out.popup', function (require) {
	"use strict";
	
	var gui = require('point_of_sale.gui');
	var rpc = require('web.rpc');
	var PopupWidget = require('point_of_sale.popups');
	var core = require('web.core');

	var _t = core._t;

    var CashInOutPopup = PopupWidget.extend({
        template: 'CashInOutPopup',
        show: function(options){
            this._super(options);
            $('.reason').focus();
            $(".amount").keypress(function (e) {
                if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
                    return false;
               }
            });
        },
        click_confirm: function(){
            var self = this;
            var name = $('.reason').val() || false;
            var amount = $('.amount').val() || false;
            if(name == '' || amount == ''){
            	self.chrome.pos_warning("FALTAN DATOS", 'Por favor ingrese los datos correctamente');
                $('.reason').focus();
                return;
            }else if(!$.isNumeric(amount)){
            	self.chrome.pos_warning("Monto no Válido", 'Por favor ingrese un monto valido');
                $('.amount').val('').focus();
                return;
            }
            var vals = {
                'name': name,
                'amount': amount,
            }
            var params = {
                model: 'pos.session',
                method: 'action_create_cash_operation',
                args: [
                	self.pos.pos_session.id, 
                	self.pos.get_cashier().id, 
                	vals, 
                	self.options.operation
                ],
            }
            rpc.query(params).then(function(result) {
                var order = self.pos.get_order();
                var operation = self.options.operation == "put_money" ? 'Ingresar Dinero' : 'Sacar Dinero'
                if(order && self.pos.config.enable_cash_in_out_receipt){
                    order.set_cash_in_out_details({
                        'operation': operation,
                        'reason': name,
                        'amount': amount,
                    });
                }
                if (self.pos.config.iface_cashdrawer){
                    self.pos.proxy.open_cashbox();
                }
                self.gui.close_popup();
                if(self.pos.config.enable_cash_in_out_receipt){
                	self.gui.show_screen('receipt');
                }else{
                	self.chrome.pos_notify("Operacion de Caja", 'Transaccion realizada con exito');
                }
            }).fail(function(err, event) {
                event.preventDefault();
                var error_body = _t('Your Internet connection is probably down.');
                if (err.data) {
                    var except = err.data;
                    error_body = except.arguments && except.arguments[0] || except.message || error_body;
                }
                self.gui.show_popup('error',{
                    'title': _t('Error: Could not Save Changes'),
                    'body': error_body,
                });
            });
        }
    });
    
    gui.define_popup({name:'cash_in_out_popup', widget: CashInOutPopup});
    
    return {
    	CashInOutPopup: CashInOutPopup,
    };

});
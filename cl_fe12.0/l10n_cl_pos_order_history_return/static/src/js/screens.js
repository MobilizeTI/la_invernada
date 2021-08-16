odoo.define('l10n_cl_pos_order_history_return.screens', function (require) {
    "use strict";

    var screens = require('pos_orders_history_return.screens');
    
	screens.PaymentScreenWidget.include({
		init: function(parent, options) {
			var self = this;
	        this._super(parent, options);
	        this.pos.get('orders').bind('add remove change', function () {
				this.renderElement();
			}, this);
		},
		renderElement: function() {
	        var self = this;
	        this._super();
	        this.$('.js_credit_note').click(function(){
	            self.click_set_credit_note();
	        });
		},
		click_set_credit_note: function(){
			var self = this;
			var options = {};
			var order = self.pos.get_order();
			options.filter_refund = order.get_credit_note_type();
			options.note_id = order.get_credit_note_reason();
			this.gui.show_popup('order_return_popup', options);
	    },
	    order_is_valid: function(force_validation) {
			var self = this;
			var res = this._super(force_validation);
			// cuando no paso la validacion en la llamada super, no validar y mostrar error
			if (!res){
				return res
			}
			var order = self.pos.get_order();
			var order_sequence = order.get_document_sequence();
			var document_class = {};
			if (order_sequence){
				var sii_sequence = self.pos.db.get_ir_sequence_by_id(order_sequence);
				if (sii_sequence.sii_document_class_id){
					document_class = self.pos.db.get_sii_document_type_by_id(sii_sequence.sii_document_class_id[0]);
				}
			}
			// en NC validar que haya ingresado el tipo de NC
			if (document_class.sii_code == 61){
				if (!order.get_credit_note_type()){
					this.gui.show_popup('error',{
			        	'title': "Datos de Nota de Credito incompletos",
			        	'body': "Por favor seleccione el tipo de Nota de credito para poder continuar",
			        });
					return false;
				}
			}
			return res;
	    }
	});
	
    screens.OrdersHistoryScreenWidget.include({
    	prepare_order_for_return: function(json) {
    		var self = this;
        	var options = this._super(json);
        	if (options.json){
        		var sequence_nc_id = false;
        		var document_class = {};
    			// buscar la secuencia para NC de las configuradas en el POS
    			// en caso de no haber secuencia, mostrar mensaje para evitar crear pedido sin folio de NC
    			for (var i = 0, len = self.pos.config.sequence_available_ids.length; i < len; i++) {
    				var sequence_id = self.pos.config.sequence_available_ids[i];
    				var sii_sequence = self.pos.db.get_ir_sequence_by_id(sequence_id);
    				if (sii_sequence.sii_document_class_id){
    					document_class = self.pos.db.get_sii_document_type_by_id(sii_sequence.sii_document_class_id[0]);
    					if (document_class.sii_code == 61){
    						sequence_nc_id = sequence_id;
    						break;
    					}
    				}
    	  		}
    			// pasar el tipo de documento de NC y los datos que so del pedido original(firma, numero de folio, etc)
    			if (sequence_nc_id){
    				options.json.sequence_id = sequence_nc_id;
    				options.json.signature = undefined;
    				options.json.origin_order_id = options.json.id;
    				options.json.sii_document_number = 0;
    			}else{
    				self.chrome.pos_warning("Devolucion de Productos", 'No hay CAF cargados para emitir Notas de Credito, por favor verifique la configuracion del TPV');
    				return false;
    			}
    			
        	}
        	return options;
        },
        set_order_for_return: function(order) {
        	var self = this;
        	var res = this._super(order);
        	// en caso de que el pedido original haya tenido cliente
			// pasar el mismo cliente a la devolucion
        	if (order.origin_order_id){
        		var origin_order = self.pos.db.orders_history_by_id[order.origin_order_id] || {};
        		if (origin_order.partner_id){
        			var partner = self.pos.db.get_partner_by_id(origin_order.partner_id[0]);
        			if (partner){
        				if (partner.responsability_id){
        					var responsability = _.filter(self.pos.responsabilities, function(responsability){ return responsability.id == partner.responsability_id[0]; });
        					if (responsability.length > 0){
        						if (responsability[0].code === 'CF'){
        							partner = null;
        							order.set_client(null);
        						}
        					}
        				}
        			}
    				if (partner){
    					order.set_client(partner);
    				}
        		}
        	}
        	return res;
        },
    });
    return screens;
});

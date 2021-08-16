odoo.define('l10n_cl_pos_order_history_return.models', function(require) {
	var models = require('point_of_sale.models');
	var models_stock = require('pos_stock_quantity.pos_stock').models;
	var time = require('web.time');
	
	models.load_models({
		model: 'pos.order.reason.nc',
		fields: ['name',],
		loaded: function(self, credit_note_reasons){
			self.db.add_credit_note_reason(credit_note_reasons);
		},
	});

	
	var _super_Order = models.Order.prototype;
	var credit_note_type_names = {
			'1': 'Anula Documento de Referencia',
			'2': 'Corrige texto Documento Referencia',
			'3': 'Corrige montos',
	};
	var _super_pos = models_stock.PosModel.prototype;
	models_stock.PosModel = models.PosModel.extend({
    	is_allow_out_of_stock: function(){
    		var order = this.get_order();
    		// cuando sea NC, no deshabilitar productos sin stock
    		if (order && order.get_document_class().sii_code == 61){
    			return true;
    		}
    		return _super_pos.is_allow_out_of_stock.call(this);
    	}
    });
    
	models.Order = models.Order.extend({
		// llamar a esta funcion para agregar datos adicionales de ser necesario
		set_fields_for_return : function(return_data_aditional) {
			var self = this;
			this.return_data_aditional = return_data_aditional;
			if (return_data_aditional.note_id){
				this.return_data_aditional.note = this.pos.db.get_credit_note_reason_by_id(return_data_aditional.note_id).name;
			}
			if (this.origin_order_id){
				var origin_order = self.pos.db.orders_history_by_id[this.origin_order_id] || {};
				if (origin_order){
					var document_class = {};
					if (origin_order.document_class_id){
						document_class = self.pos.db.get_sii_document_type_by_id(origin_order.document_class_id[0]);
					}
					
					self.set_referencias([{
		    			folio: origin_order.sii_document_number,
		    			tpo_doc: document_class.name,
		    			date: time.date_to_str(time.auto_str_to_date(origin_order.date_order)),
		    			sii_code: document_class.sii_code,
		    			razon: self.return_data_aditional.note,
		    		}]);
				}
			}
			this.trigger('change', this);
            this.trigger('new_updates_to_send');
		},
		get_credit_note_type(){
			return (this.return_data_aditional || {}).filter_refund;
		},
		get_credit_note_reason(){
			return (this.return_data_aditional || {}).note_id;
		},
		get_credit_note_type_text(){
			var credit_note_type = "Seleccione tipo de NC";
			var filter_refund = this.get_credit_note_type();
			if (filter_refund){
				credit_note_type = credit_note_type_names[filter_refund];
			}
			return credit_note_type;
		}
	});

});
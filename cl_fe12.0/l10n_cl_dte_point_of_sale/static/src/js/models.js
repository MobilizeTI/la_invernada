odoo.define('l10n_cl_dte_point_of_sale.models', function (require) {
"use strict";

// implementaciónen el lado del cliente de firma
var models = require('point_of_sale.models');
var models_history = require('pos_orders_history.models');
var utils = require('web.utils');
var core = require('web.core');
var rpc = require('web.rpc');
var time = require('web.time');
var _t = core._t;

var modules = models.PosModel.prototype.models;
var round_pr = utils.round_precision;

for(var i=0; i<modules.length; i++){
	var model=modules[i];
	if(model.model === 'res.company'){
		model.fields.push('activity_description','street','city', 'dte_resolution_date', 'dte_resolution_number', 'website_portal_boletas', 'sii_regional_office_id');
	}
	if(model.model === 'res.partner'){
		model.fields.push('document_number','activity_description','document_type_id', 'state_id', 'city_id', 'dte_email', 'responsability_id', 'property_payment_term_id', 'is_company', 'parent_id', 'sync');
	}
	if (model.model == 'product.product') {
		model.fields.push('name');
	}
	if (model.model == 'res.country') {
		model.fields.push('code');
	}
	if (model.model == 'account.tax') {
		model.fields.push('uom_id');
	}
}

models.load_models({
	model: 'res.partner',
	fields: ['document_number',],
	domain: function(self){ return [['id','=', self.company.partner_id[0]]]; },
      	loaded: function(self, dn){
      		self.company.document_number = dn[0].document_number;
      	},
});

models.load_models({
	model: 'sii.document_type',
	fields: ['id', 'name', 'sii_code'],
		loaded: function(self, dt){
			self.sii_document_types = dt;
		},
});

models.load_models({
	model: 'sii.activity.description',
	fields: ['id', 'name'],
		loaded: function(self, ad){
			self.sii_activities = ad;
		},
});

models.load_models({
	model: 'res.country.state',
	fields: ['id', 'name', 'country_id'],
		loaded: function(self, st){
			self.states = st;
		},
});

models.load_models({
	model: 'res.city',
	fields: ['id', 'name', 'state_id', 'country_id'],
		loaded: function(self, ct){
			self.cities = ct;
			self.cities_by_id = {};
            _.each(ct, function(city){
                self.cities_by_id[city.id] = city;
            });
		},
});

models.load_models({
	model: 'sii.responsability',
	fields: ['id', 'name', 'tp_sii_code', 'code'],
      	loaded: function(self, rs){
      		self.responsabilities = rs;
      	},
});

models.load_fields("pos.session", ["document_available_ids"]);

models.load_models([{
	model:  'ir.sequence',
	domain: function(self){
		return [['id', 'in', self.config.sequence_available_ids]];
	},
	fields: ['sii_document_class_id', 'name', 'show_in_pos', 'mode_online', 'correct_folios_automatic'],
	loaded: function(self, sequences){
		self.db.add_ir_sequence(sequences);
	}
},{
	model:  'sii.document_class',
	domain: function(self){
		return [['id','in',self.db.document_class_ids]];
	},
	fields: ['id', 'name', 'sii_code', 'dte'],
	loaded: function(self, sri_document_types){
		self.db.add_sii_document_types(sri_document_types);
	}
},{
	model:  'pos.session.document.available',
	domain: function(self){
		return [['pos_session_id','=',self.pos_session.id]];
	},
	fields: ['caf_files', 'next_document_number', 'last_document_number', 'document_class_id', 'sequence_id'],
	loaded: function(self, sri_document_availables){
		self.db.add_sii_document_info_data(sri_document_availables);
	}
}]);

var _super_pos_model_history = models_history.PosModel.prototype;
models_history.PosModel = models_history.PosModel.extend({
	get_domain_for_order_history(query){
		var domain = _super_pos_model_history.get_domain_for_order_history.apply(this, arguments);
		if (query){
			domain.pop(['pos_history_reference_uid','=',query]);
			domain.push(['sii_document_number','=',query]);
        } 
		return domain;
    }
});

var PosModelSuper = models.PosModel.prototype;
models.PosModel = models.PosModel.extend({
	initialize: function(session, attributes) {
		var res = PosModelSuper.initialize.call(this, session, attributes);
		var self = this;
		// siempre que se cambie la orden actual,
		// refrescar los datos segun el tipo de documento de la nueva orden actual
		self.bind('change:selectedOrder', function () {
			self.refresh_document_data();
        }, self);
		return res;
	},
	// actualizar la sequencia del documento
	// esto cuando se cambie la orden actualmente seleccionada
	refresh_document_data: function(){
		var document_sequence = undefined;
		if (this.config.default_sequence_id){
			document_sequence = this.config.default_sequence_id[0];
		}
		var order = this.get_order();
		if (order){
			if (order.get_document_sequence()){
				document_sequence = order.get_document_sequence();
			}
		}
		var new_document_data = this.db.get_sii_document_info_by_sequence(document_sequence);
		this.set_current_document_data(new_document_data);
	},
	// cambiar la data de secuencias a la nueva data
	// con esta data es que se generara el documento actual
	set_current_document_data: function(new_document_data){
		this.current_document_data = new_document_data;
		return;
	},
	get_current_document_data: function(){
		return this.current_document_data || {};
	},
	set_next_document_number: function(document_sequence, next_document_number){
		//incrementar en 1 la secuencia por defecto
		//cuando se pasen los parametros, actualizar los datos a esos parametros especificados
		// en caso que el tipo de documento actual no sea el mismo que el documento que se pasa
		// actualizar los datos del documento actual
		var self = this;
		if (self.get_current_document_data().sequence_id[0] !== document_sequence){
			var new_document_data = self.db.get_sii_document_info_by_sequence(document_sequence);
			this.set_current_document_data(new_document_data);
		}
		if (next_document_number == undefined){
			next_document_number =  self.current_document_data.next_document_number + 1;
		}
		// validar cuando se este en el ultimo numero disponible
		// pasar a la siguiente secuencia disponible
		// en caso de no haber mas secuencias, no hacer nada
		// el sistema no permitira emitir mas pedidos xq no hay documentos disponibles
		if (next_document_number > self.current_document_data.last_document_number){
			var caf_files = JSON.parse(self.current_document_data.caf_files);
			for (var i = 0, len = caf_files.length; i < len; i++) {
				var document_info = caf_files[i];
				// si hay una secuencia, tomar el primer numero de la siguiente secuencia
				// puedo tener una secuencia del 1 al 10 y la siguiente secuencia es del 20 al 30
				// al terminar la secuencia de 10, el proximo numero consecutivo seria el 11
				// pero debemos tomar la secuencia del 20, 
				// por ello comparar que el primer numero de la siguiente secuencia(20) sea mayor al ultimo numero generado(11)
                if (parseInt(document_info.AUTORIZACION.CAF.DA.RNG.D) >= next_document_number && next_document_number < parseInt(document_info.AUTORIZACION.CAF.DA.RNG.H)){
                	next_document_number = parseInt(document_info.AUTORIZACION.CAF.DA.RNG.D);
                	this.current_document_data.last_document_number = parseInt(document_info.AUTORIZACION.CAF.DA.RNG.H);
                    break;
                // en caso que no se cumpla la condicion anterior, tambien verificar que la secuencia este dentro del rango de una autoriazacion valida
                // esto se da cuando se quedan pedidos en cola, y el ultimo pedido enviado al server fue el 9
                // pero se emitio el documento 10, luego el 20 y 21( estos 3 pedidos no se enviaron al server)
                // al enviar esos pedidos al server, la sesion tiene el rango vigente del 1 al 10, pero deberia ser del 20 al 30
                // y el siguiente numero seria el 22, asi que tomar la autorizacion dentro de ese rango, 
                // pero tomar el siguiente numero como el primero de la secuencia(el primero seria 20, pero el numero deberia ser el 22 en el ejemplo)
                }else if (next_document_number >= parseInt(document_info.AUTORIZACION.CAF.DA.RNG.D) && next_document_number < parseInt(document_info.AUTORIZACION.CAF.DA.RNG.H)){
                	this.current_document_data.last_document_number = parseInt(document_info.AUTORIZACION.CAF.DA.RNG.H);
                    break;
                }
			}
		}
		this.current_document_data.next_document_number = next_document_number;
	},
	get_next_document_number: function(){
		var self = this;
		var next_document_number = this.get_current_document_data().next_document_number || 0;
		return next_document_number.toString();
	},
	assing_document_number_to_order: function(order){
		//obtener el numero para la orden dada y generar el siguiente numero de orden
		var self = this;
		var document_sequence = order.get_document_sequence();
		if (document_sequence && order.paymentlines.length > 0 && !order.sii_document_number){
			if (self.get_current_document_data().sequence_id[0] !== document_sequence){
				var new_document_data = self.db.get_sii_document_info_by_sequence(document_sequence);
				self.set_current_document_data(new_document_data);
			}
			// obtener el siguiente numero del pedido
			// y calcular el proximo numero para el siguiente pedido
			order.sii_document_number = self.get_next_document_number();
			self.set_next_document_number(document_sequence);
			var amount = Math.round(order.get_total_with_tax());
			if (amount !== 0){
				order.signature = order.timbrar(order);
			}
		}
	},
	get_documents_remaining: function(){
		var current_document_data = this.get_current_document_data();
		var documents_remaining = (current_document_data.last_document_number || 0) - (current_document_data.next_document_number || 0)
		//cuando la resta del ultimo con el primero da un negativo, pasarlo a 0
		//esto se da cuando se termina la secuencia, el numero actual es > al utlimo numero
		//la resta dara un negativo, asi que corregirlo para visualizar 0 en lugar de -1
		if (documents_remaining < 0){
			documents_remaining = 0;
		}
		//la diferencia debe ser inclsive(incluyendo el numero actual)
		//solo en caso de no haber documentos disponibles no sumar 1
		if (documents_remaining > 0){
			documents_remaining += 1;
		}
		//cuando esta en la ultima secuencia, se debe dar 1 como documento disponible
		if (current_document_data.next_document_number === current_document_data.last_document_number && current_document_data.next_document_number > 0){
			documents_remaining = 1;
		}
		return documents_remaining;
	},
	get_next_document_number_text: function(){
		var next_document_number = this.get_next_document_number();
		var next_document_number_msj = "<b style='color: green;'>%(next_document_number)s</b>";
		next_document_number_msj = _.str.sprintf(next_document_number_msj, { 
			next_document_number: next_document_number
		});
		return next_document_number_msj;
	},
	get_documents_remaining_text: function(){
		var documents_remaining = this.get_documents_remaining();
		var documents_min = 10; //TODO: tomar el numero minimo desde la configuracion de contabilidad(en la compañia)
		var color = documents_remaining < documents_min ? 'red': 'green';
		var next_document_number_msj = "Disponibles <b style='color: %(color)s;'>%(documents_remaining)s</b>";
		if (this.is_mobile){
			next_document_number_msj = "<b style='color: %(color)s;'>De %(documents_remaining)s</b>";
		}
		next_document_number_msj = _.str.sprintf(next_document_number_msj, {color: color, 
			documents_remaining: documents_remaining
		});
		return next_document_number_msj;
	},
	refresh_next_document_number: function() {
		this.chrome.$('.js_msg_next_document_number').html(this.get_next_document_number_text());
		this.chrome.$('.js_msg_documents_remaining').html(this.get_documents_remaining_text());
	},
	send_order_pending_and_refresh_session: function(orders_pending, opts) {
  		var self = this;
  		var number_data = {};
  		var number_data_by_document_type = {};
  		for (var i = 0, len = self.config.sequence_available_ids.length; i < len; i++) {
			var sequence_id = self.config.sequence_available_ids[i];
			number_data_by_document_type[sequence_id] = 0;
  		}
  		var sequence_number = "";
  		//recorrer cada pedido pendiente y tomar el numero mayor
  		//para calcular el siguiente numero disponible
  		_(orders_pending).each(function(order_data){
  			var order = order_data.data;
  			if (order.sii_document_number && order.sequence_id){
  				sequence_number = parseInt(order.sii_document_number);
  				var document_data = self.db.get_sii_document_info_by_sequence(order.sequence_id);
				if (document_data && sequence_number > document_data.next_document_number){
					number_data_by_document_type[order.sequence_id] = sequence_number;
				}
  			}
  		});
  		for (var i = 0, len = self.config.sequence_available_ids.length; i < len; i++) {
  			var sequence_id = self.config.sequence_available_ids[i];
  			if (number_data_by_document_type[sequence_id] > 0){
	  			self.set_next_document_number(sequence_id, number_data_by_document_type[sequence_id]+1);
	  		}
  		}
  		return PosModelSuper.push_order.call(this, null, opts);
  	},
	push_order: function(order, opts) {
		var self = this;
		var pushed_order_deffered = new $.Deferred();
		if(order){
			var document_sequence_id = order.get_document_sequence();
			var sii_sequence = self.db.get_ir_sequence_by_id(document_sequence_id);
			if (sii_sequence && sii_sequence.mode_online && order.paymentlines.length > 0 && !order.sii_document_number){
				if (self.get_current_document_data().sequence_id[0] !== document_sequence_id){
					var new_document_data = self.db.get_sii_document_info_by_sequence(document_sequence_id);
					self.set_current_document_data(new_document_data);
				}
				// obtener el siguiente numero del pedido
				var sii_document_number = self.get_next_document_number();
				var params = {
					model: 'pos.order',
					method: 'check_folios',
					args: [sii_document_number, document_sequence_id]
				}
				rpc.query(params)
					.then(function(result){
						if (result && result[0]){
				  			//obtener y generar el siguiente numero
							self.assing_document_number_to_order(order);
							var res = PosModelSuper.push_order.call(self, order, opts);
							pushed_order_deffered.resolve();
							res.resolve();
							return res;
						} else if (sii_sequence.correct_folios_automatic){
				  			// refrescar el siguiente numero
							self.set_next_document_number(document_sequence_id, result[1]);
							self.assing_document_number_to_order(order);
							var res = PosModelSuper.push_order.call(self, order, opts);
							pushed_order_deffered.resolve();
							res.resolve();
							return res;
						} else{
							self.gui.play_sound('error');
							self.gui.show_popup('confirm',{
								'title': 'Folio Repetido',
								'body': _.str.sprintf("El folio %(document_number)s esta repetido, " +
										"Desea Asignar el ultimo folio disponible automaticamente?. " +
										"Caso contrario contacte con su administrador",  {
											document_number: sii_document_number,
								}),
								confirm: function(){
		                        	// refrescar el siguiente numero
									self.set_next_document_number(document_sequence_id, result[1]);
									self.assing_document_number_to_order(order);
									var res = PosModelSuper.push_order.call(self, order, opts);
									pushed_order_deffered.resolve();
									res.resolve();
									return res;
								},
								cancel: function(){
									pushed_order_deffered.reject({no_show_error: true});
								},
							});
						}
					}).fail(function(error, ev){
						ev.preventDefault();
				  		// evitar que se muestre la ventana de recibo en la funcion _handleFailedPushForInvoice
						pushed_order_deffered.reject({no_show_error: true});
						if (error.code === 200) {    // OpenERP Server Errors
							self.gui.show_popup('error',{
				                'title': _t("Server Error"),
				                'body': error.data.message || _t('The server encountered an error while receiving your order.'),
				            });
				        } else{
				        	self.gui.show_popup('error-traceback',{
								'title': error.data.message || _t("Server Error"),
								'body': error.data.debug || 'No se puede conectar con el servidor para validar el folio, por favor asegurese de tener conexion con el servidor.',
							});	
				        }
					});
				return pushed_order_deffered;
			}else{
				// obtener y generar el siguiente numero
				self.assing_document_number_to_order(order);
			}
		}else{
			var orders_pending = self.db.get_orders();
			if (orders_pending.length > 0){
	  	    	return self.send_order_pending_and_refresh_session(orders_pending, opts);
			}
		}
		var res = PosModelSuper.push_order.call(self, order, opts);
		pushed_order_deffered.resolve();
		return pushed_order_deffered;
	},
	get_current_document_type_name: function () {
        var self = this;
		var name = 'Tipo de Documento';
        var order = self.get_order();
        if (order) {
            if (order.get_document_sequence()) {
            	var sii_sequence = self.db.get_ir_sequence_by_id(order.get_document_sequence());
            	if (sii_sequence){
	            	if (sii_sequence.sii_document_class_id){
	            		name = self.db.get_sii_document_type_by_id(sii_sequence.sii_document_class_id[0]).name;
	            	}else{
	            		name = sii_sequence.name;
	            	}
            	}
            }
        }
        return name;
    },
    get_documents_type_for_selection: function () {
    	var self = this;
    	var document_sequences = [];
		for (var i = 0, len = self.config.sequence_available_ids.length; i < len; i++) {
			var sequence_id = self.config.sequence_available_ids[i];
			var sequence = self.db.get_ir_sequence_by_id(sequence_id);
			if (sequence.show_in_pos){
				var item_label = sequence.name;
            	if (sequence.sii_document_class_id){
            		item_label = self.db.get_sii_document_type_by_id(sequence.sii_document_class_id[0]).name;
            	}
				document_sequences.push({
					label: item_label,
					item: sequence,
				})	
			}
		}
		return document_sequences;
    }
});

var _super_order_line = models.Orderline.prototype;
models.Orderline = models.Orderline.extend({
	_compute_all: function(tax, base_amount, quantity, uom_id) {
		if (tax.amount_type === 'fixed') {
			var amount_tax = tax.amount;
			if (tax.uom_id && uom_id){
				var tax_uom = this.pos.units_by_id[tax.uom_id[0]];
				if (tax.uom_id !== uom_id){
					var factor = (1 / tax_uom.factor);
					amount_tax = (amount_tax / factor);
				}
			}
			var sign_base_amount = Math.sign(base_amount) || 1;
			// Since base amount has been computed with quantity
			// we take the abs of quantity
			// Same logic as bb72dea98de4dae8f59e397f232a0636411d37ce
			return amount_tax * sign_base_amount * Math.abs(quantity);
		}
		if ((tax.amount_type === 'percent' && !tax.price_include) || (tax.amount_type === 'division' && tax.price_include)){
			return base_amount * tax.amount / 100;
		}
		if (tax.amount_type === 'percent' && tax.price_include){
			return base_amount - (base_amount / (1 + tax.amount / 100));
		}
		if (tax.amount_type === 'division' && !tax.price_include) {
			return base_amount / (1 - tax.amount / 100) - base_amount;
		}
		return false;
	},
	compute_all: function(taxes, price_unit, quantity, currency_rounding, no_map_tax, uom_id) {
		var self = this;
		var list_taxes = [];
		var currency_rounding_bak = currency_rounding;
		if (this.pos.company.tax_calculation_rounding_method == "round_globally"){
			currency_rounding = currency_rounding * 0.00001;
		}
		var total_excluded = round_pr(price_unit * quantity, currency_rounding);
		var total_included = total_excluded;
		var base = total_excluded;
		_(taxes).each(function(tax) {
			if (!no_map_tax){
				tax = self._map_tax_fiscal_position(tax);
			}
			if (!tax){
				return;
			}
			if (tax.amount_type === 'group'){
				var ret = self.compute_all(tax.children_tax_ids, price_unit, quantity, currency_rounding, uom_id);
				total_excluded = ret.total_excluded;
				base = ret.total_excluded;
				total_included = ret.total_included;
				list_taxes = list_taxes.concat(ret.taxes);
			} else {
				var tax_amount = self._compute_all(tax, base, quantity, uom_id);
				tax_amount = round_pr(tax_amount, currency_rounding);
				if (tax_amount){
					if (tax.price_include) {
						total_excluded -= tax_amount;
						base -= tax_amount;
					} else {
						total_included += tax_amount;
					}
					if (tax.include_base_amount) {
						base += tax_amount;
					}
					var data = {
						id: tax.id,
						amount: tax_amount,
						name: tax.name,
						base: base,
					};
					list_taxes.push(data);
				}
			}
		});
		return {
			taxes: list_taxes,
			total_excluded: round_pr(total_excluded, currency_rounding_bak),
			total_included: round_pr(total_included, currency_rounding_bak)
		};
	},
	get_all_prices: function(){
		var price_unit = this.get_price_reduce();
		var taxtotal = 0;
		var product =  this.get_product();
		var taxes_ids = product.taxes_id;
		var taxes =  this.pos.taxes;
		var taxdetail = {};
		var product_taxes = [];

		_(taxes_ids).each(function(el){
			product_taxes.push(_.detect(taxes, function(t){
				return t.id === el;
			}));
		});

		var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding, this.get_unit());
		_(all_taxes.taxes).each(function(tax) {
			taxtotal += tax.amount;
			taxdetail[tax.id] = tax.amount;
		});

		return {
			"priceWithTax": all_taxes.total_included,
			"priceWithoutTax": all_taxes.total_excluded,
			"tax": taxtotal,
			"taxDetails": taxdetail,
		};
	},
	compute_fixed_price: function (price) {
        var order = this.order;
        if(order.fiscal_position) {
            var taxes = this.get_taxes();
            var mapped_included_taxes = [];
            var uom_id = false;
            var self = this;
            _(taxes).each(function(tax) {
                var line_tax = self._map_tax_fiscal_position(tax);
                if(tax.price_include && line_tax.id != tax.id){
                	uom_id = self.get_unit();
                    mapped_included_taxes.push(tax);
                }
            });

            if (mapped_included_taxes.length > 0) {
                return this.compute_all(mapped_included_taxes, price, 1, order.pos.currency.rounding, true, uom_id).total_excluded;
            }
        }
        return price;
    },

});

var _super_order = models.Order.prototype;
models.Order = models.Order.extend({
	initialize: function(attributes, options) {
		var self = this;
		self.referencias = [];
		var res = _super_order.initialize.call(this, attributes, options);
		if (self.sequence_id == undefined && self.pos.config.default_sequence_id){
			self.set_document_sequence(self.pos.config.default_sequence_id[0]);
		}
		return res;
    },
	export_as_JSON: function() {
		var json = _super_order.export_as_JSON.apply(this,arguments);
		json.sequence_id = this.sequence_id;
		json.sii_document_number = this.sii_document_number;
		json.signature = this.signature;
		json.orden_numero = this.orden_numero;
		json.referencias = this.referencias;
		json.finalized = this.finalized;
		return json;
	},
    init_from_JSON: function(json) {// carga pedido individual
    	_super_order.init_from_JSON.apply(this,arguments);
    	this.sequence_id = json.sequence_id;
    	this.sii_document_number = json.sii_document_number;
    	this.signature = json.signature;
    	this.orden_numero = json.orden_numero;
    	this.referencias = json.referencias;
    	this.finalized = json.finalized;
	},
	set_document_sequence: function(new_sequence) {
    	var new_document_data = this.pos.db.get_sii_document_info_by_sequence(new_sequence);
    	if (new_document_data == undefined){
    		this.pos.gui.show_popup('error', 'No hay CAF cargados para el tipo de documento seleccionado');
    		return;
    	}
    	if (new_document_data.caf_files.length <=0){
    		this.pos.gui.show_popup('error', 'No hay CAF vigentes para el tipo de documento seleccionado');
    		return;
    	}
    	this.sequence_id = new_sequence;
    	// validar que el caf no este expirado
		if (!this.es_boleta()){
			var next_document_number = new_document_data.next_document_number;
			var caf_files = JSON.parse(new_document_data.caf_files);
			var is_expired = false;
			var today = time.date_to_str(new Date());
			for (var i = 0, len = caf_files.length; i < len; i++) {
				var document_info = caf_files[i];
				var expiration_date = time.date_to_str(moment(document_info.AUTORIZACION.CAF.DA.FA).add(6, 'months').toDate());
				if (next_document_number >= parseInt(document_info.AUTORIZACION.CAF.DA.RNG.D) && next_document_number < parseInt(document_info.AUTORIZACION.CAF.DA.RNG.H)){
					if (today > expiration_date){
						is_expired = true;
						break;
					}	
				}
			}
			if (is_expired){
				var has_caf = false;
				for (var i = 0, len = caf_files.length; i < len; i++) {
					var document_info = caf_files[i];
					var expiration_date = time.date_to_str(moment(document_info.AUTORIZACION.CAF.DA.FA).add(6, 'months').toDate());
					if (today > expiration_date){
						continue;
					}	
					if (parseInt(document_info.AUTORIZACION.CAF.DA.RNG.D) >= next_document_number && next_document_number < parseInt(document_info.AUTORIZACION.CAF.DA.RNG.H)){
						new_document_data.next_document_number = parseInt(document_info.AUTORIZACION.CAF.DA.RNG.D);
						new_document_data.last_document_number = parseInt(document_info.AUTORIZACION.CAF.DA.RNG.H);
						has_caf = true;
	                    break;
					}
				}
				if (!has_caf){
		    		this.pos.gui.show_popup('error', 'No hay CAF cargados para el tipo de documento seleccionado');
		    		return;
				}
			}
		}
		this.pos.set_current_document_data(new_document_data);
    	this.trigger('change');
    },
    get_document_sequence: function() {
    	return this.sequence_id;
    },
    get_document_class: function() {
    	var document_class = {}
    	var sii_sequence = this.pos.db.get_ir_sequence_by_id(this.get_document_sequence());
    	if ((sii_sequence || {}).sii_document_class_id){
    		document_class = this.pos.db.get_sii_document_type_by_id(sii_sequence.sii_document_class_id[0]);
    	}
    	return document_class;
    },
    get_referencias: function(){
    	return this.referencias || [];
    },
    set_referencias: function(referencias){
    	this.referencias = referencias;
    },
	export_for_printing: function() {
		var json = _super_order.export_for_printing.apply(this,arguments);
		json.company.document_number = this.pos.company.document_number;
		json.company.activity_description = this.pos.company.activity_description[1];
		json.company.street = this.pos.company.street;
		json.company.city = this.pos.company.city;
		json.company.dte_resolution_date = this.pos.company.dte_resolution_date;
		json.company.dte_resolution_number = this.pos.company.dte_resolution_number;
		json.company.website_portal_boletas = this.pos.company.website_portal_boletas;
		json.sii_document_number = this.sii_document_number;
		json.orden_numero = this.orden_numero;
		if(this.sequence_id){
			var sii_sequence = this.pos.db.get_ir_sequence_by_id(this.sequence_id);
        	if (sii_sequence.sii_document_class_id){
        		json.nombre_documento = this.pos.db.get_sii_document_type_by_id(sii_sequence.sii_document_class_id[0]).name;
        	}else{
        		json.nombre_documento = sii_sequence.name;
        	}
		}
		var d = this.creation_date;
		var curr_date = this.completa_cero(d.getDate());
		var curr_month = this.completa_cero(d.getMonth() + 1); // Months
																	// are zero
																	// based
		var curr_year = d.getFullYear();
		var hours = d.getHours();
		var minutes = d.getMinutes();
		var seconds = d.getSeconds();
		var date = curr_year + '-' + curr_month + '-' + curr_date + ' ' +
			this.completa_cero(hours) + ':' + this.completa_cero(minutes) + ':' + this.completa_cero(seconds);
		json.creation_date = date;
		json.barcode = this.barcode_pdf417();
		json.exento = this.get_total_exento();
		json.referencias = this.get_referencias();
		json.client = this.get('client');
		return json;
	},
    // esto devolvera True si es Boleta(independiente si es exenta o afecta)
    // para diferenciar solo si es una factura o una boleta
	es_boleta: function(){
		if (this.sequence_id){
			var sii_sequence = this.pos.db.get_ir_sequence_by_id(this.sequence_id);
			if (sii_sequence.sii_document_class_id){
				var document_class = this.pos.db.get_sii_document_type_by_id(sii_sequence.sii_document_class_id[0]);
				if (_.contains([35, 38, 39, 41, 70, 71], document_class.sii_code)){
					return true;	
				}
			}
		}
		return false;
	},
    // esto devolvera True si es Boleta exenta(sii_code = 41)
	es_boleta_exenta: function(check_marcar=false){
		if(!this.es_boleta()){
			return false;
		}
		if (this.sequence_id){
			var sii_sequence = this.pos.db.get_ir_sequence_by_id(this.sequence_id);
			if (sii_sequence.sii_document_class_id){
				var document_class = this.pos.db.get_sii_document_type_by_id(sii_sequence.sii_document_class_id[0]);
				if (document_class.sii_code === 41){
					return true;	
				}
			}
		}
		return false;
    },
    // esto devolvera True si es Boleta afecta(sii_code = 39)
	es_boleta_afecta: function(check_marcar=false){
		if(!this.es_boleta()){
			return false;
		}
		if (this.sequence_id){
			var sii_sequence = this.pos.db.get_ir_sequence_by_id(this.sequence_id);
			if (sii_sequence.sii_document_class_id){
				var document_class = this.pos.db.get_sii_document_type_by_id(sii_sequence.sii_document_class_id[0]);
				if (document_class.sii_code === 39){
					return true;	
				}
			}
		}
		return false;
	},
    get_total_exento:function(){
    	var taxes =  this.pos.taxes;
    	var exento = 0;
    	this.orderlines.each(function(line){
    		var product =  line.get_product();
    		var taxes_ids = product.taxes_id;
    		_(taxes_ids).each(function(el){
    			_.detect(taxes,function(t){
    				if(t.id === el && t.amount === 0){
    					exento += (line.get_unit_price() * line.get_quantity());
    				}
    			});
    		});
    	});
    	return exento;
    },
	completa_cero(val){
    	if (parseInt(val) < 10){
    		return '0' + val;
    	}
    	return val;
    },
    encode: function(caracter){
    	var string = "";
    	for (var i=0; i< caracter.length; i++){
    		var l = caracter[i];
    		if(l.charCodeAt() >= 160){
    			l = "&#"+ l.charCodeAt()+';';
    		}
    		if(i < 40){
    			string += l;
    		}
    	}
    	return string;
	},
	timbrar: function(order){
		if (order.signature){ // no firmar otra vez
			return order.signature;
		}
		var today = time.date_to_str(new Date());
		var document_class = this.get_document_class();
		if (! document_class.dte){
			return "";
		}
		var caf_files = JSON.parse(this.pos.current_document_data.caf_files);
		var caf_file = false;
		for (var x in caf_files){
			var expiration_date = time.date_to_str(moment(caf_files[x].AUTORIZACION.CAF.DA.FA).add(6, 'months').toDate());
			if (today > expiration_date){
				continue;
			}	
			if(parseInt(order.sii_document_number) >= parseInt(caf_files[x].AUTORIZACION.CAF.DA.RNG.D) && parseInt(order.sii_document_number) <= parseInt(caf_files[x].AUTORIZACION.CAF.DA.RNG.H)){
				caf_file =caf_files[x]
			}
		}
		if (!caf_file){
			this.pos.gui.show_popup('error',_t('No quedan más Folios Disponibles'));
			return false;
		}
		var priv_key = caf_file.AUTORIZACION.RSASK;
		var pki = forge.pki;
		var privateKey = pki.privateKeyFromPem(priv_key);
		var md = forge.md.sha1.create();
		var partner_id = this.get_client();
		if(!partner_id){
			partner_id = {};
			partner_id.name = "Usuario Anonimo";
		}
		if(!partner_id.document_number){
			partner_id.document_number = "66666666-6";
		}
		var product_name = false;
		var ols = order.orderlines.models;
		var ols2 = ols;
		for (var p in ols){
			var es_menor = true;
			for(var i in ols2){
				if(ols[p].id !== ols2[i].id && ols[p].id > ols2[i].id){
					es_menor = false;
				}
				if(es_menor === true){
					product_name = this.encode(ols[p].product.name);
				}
			}
		}
		var d = order.validation_date || new Date();
		if (! (d instanceof Date)){
			d = new Date(d);
		}
		var curr_date = this.completa_cero(d.getDate());
		var curr_month = this.completa_cero(d.getMonth() + 1); // Months
																// are zero
																// based
		var curr_year = d.getFullYear();
		var hours = d.getHours();
		var minutes = d.getMinutes();
		var seconds = d.getSeconds();
		var date = curr_year + '-' + curr_month + '-' + curr_date + 'T' +
			this.completa_cero(hours) + ':' + this.completa_cero(minutes) + ':' + this.completa_cero(seconds);
		var rut_emisor = this.pos.company.document_number.replace('.','').replace('.','');
		if (rut_emisor.charAt(0) == "0"){
			rut_emisor = rut_emisor.substr(1);
		}
		
		var string='<DD>' +
			'<RE>' + rut_emisor + '</RE>' +
			'<TD>' + document_class.sii_code + '</TD>' +
			'<F>' + order.sii_document_number + '</F>' +
			'<FE>' + curr_year + '-' + curr_month + '-' + curr_date + '</FE>' +
			'<RR>' + partner_id.document_number.replace('.','').replace('.','') +'</RR>' +
			'<RSR>' + this.encode(partner_id.name) + '</RSR>' +
			'<MNT>' + Math.round(this.get_total_with_tax()) + '</MNT>' +
			'<IT1>' + product_name + '</IT1>' +
			'<CAF version="1.0"><DA><RE>' + caf_file.AUTORIZACION.CAF.DA.RE + '</RE>' +
				'<RS>' + caf_file.AUTORIZACION.CAF.DA.RS + '</RS>' +
				'<TD>' + caf_file.AUTORIZACION.CAF.DA.TD + '</TD>' +
				'<RNG><D>' + caf_file.AUTORIZACION.CAF.DA.RNG.D + '</D><H>' + caf_file.AUTORIZACION.CAF.DA.RNG.H + '</H></RNG>' +
				'<FA>' + caf_file.AUTORIZACION.CAF.DA.FA + '</FA>' +
				'<RSAPK><M>' + caf_file.AUTORIZACION.CAF.DA.RSAPK.M + '</M><E>' + caf_file.AUTORIZACION.CAF.DA.RSAPK.E + '</E></RSAPK>' +
				'<IDK>' + caf_file.AUTORIZACION.CAF.DA.IDK + '</IDK>' +
				'</DA>' +
				'<FRMA algoritmo="SHA1withRSA">' + caf_file.AUTORIZACION.CAF.FRMA["#text"] + '</FRMA>' +
			'</CAF>'+
			'<TSTED>' + date + '</TSTED></DD>';
		md.update(string);
		var signature = forge.util.encode64(privateKey.sign(md));
		string = '<TED version="1.0">' + string + '<FRMT algoritmo="SHA1withRSA">' + signature + '</FRMT></TED>';
		return string;
	},
    barcode_pdf417: function(){
    	var order = this.pos.get_order();
    	if (!order.sequence_id || !order.sii_document_number){
    		return false;
    	}
    	var document_class = this.get_document_class();
		if (! document_class.dte){
			return false;
		}
    	PDF417.ROWHEIGHT = 2;
    	PDF417.init(order.signature, 6);
    	var barcode = PDF417.getBarcodeArray();
    	var bw = 2;
    	var bh = 2;
    	var canvas = document.createElement('canvas');
    	canvas.width = bw * barcode['num_cols'];
    	canvas.height = 255;
    	var ctx = canvas.getContext('2d');
    	var y = 0;
    	for (var r = 0; r < barcode['num_rows']; ++r) {
    		var x = 0;
    		for (var c = 0; c < barcode['num_cols']; ++c) {
    			if (barcode['bcode'][r][c] == 1) {
    				ctx.fillRect(x, y, bw, bh);
    			}
    			x += bw;
    		}
    		y += bh;
    	}
    	return canvas.toDataURL("image/png");
	},
});

});

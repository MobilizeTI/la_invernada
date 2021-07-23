odoo.define('l10n_cl_dte_point_of_sale.DB2', function (require) {
"use strict";

var PosDB = require('point_of_sale.DB');
var PosDBHistory = require('pos_orders_history.db');

PosDB.include({	
	init : function(options) {
		options = options || {};
        var res = this._super(options);
		this.sequences_by_id = {};
		this.document_class_ids = [];
		this.sii_document_type_by_id = {};
		this.sii_document_type_by_type = {};
		this.sii_document_info_by_sequence = {};
		this.sii_document_info_by_type = {};
		return res;
	},
	_partner_search_string: function(partner){
        var str =  partner.name;
        if(partner.document_number){
            str += '|' + partner.document_number;
            str += '|' + partner.document_number.replace('.','');
        }
        if(partner.barcode){
            str += '|' + partner.barcode;
        }
        if(partner.address){
            str += '|' + partner.address;
        }
        if(partner.phone){
            str += '|' + partner.phone.split(' ').join('');
        }
        if(partner.mobile){
            str += '|' + partner.mobile.split(' ').join('');
        }
        if(partner.email){
            str += '|' + partner.email;
        }
        str = '' + partner.id + ':' + str.replace(':','') + '\n';
        return str;
    },
	add_ir_sequence: function(sequences) {
		var self = this;
		for (var i = 0, len = sequences.length; i < len; i++) {
			var ir_sequence = sequences[i];
			this.sequences_by_id[ir_sequence.id] = ir_sequence;
			if (ir_sequence.sii_document_class_id){
				if (!_.contains(self.document_class_ids, ir_sequence.sii_document_class_id[0])){
					self.document_class_ids.push(ir_sequence.sii_document_class_id[0]);
				}	
			}
		}
	},
	add_sii_document_types: function(sii_document_types) {
		var self = this;
		for (var i = 0, len = sii_document_types.length; i < len; i++) {
			var sii_document_class = sii_document_types[i];
			self.sii_document_type_by_id[sii_document_class.id] = sii_document_class;
			self.sii_document_type_by_type[sii_document_class.sii_code] = sii_document_class;
		}
	},
	// data de pos.session.document.available que tiene la informacion
	// de numero actual y ultimo numero por tipo de documento
	add_sii_document_info_data: function(sri_documents_info) {
		for (var i = 0, len = sri_documents_info.length; i < len; i++) {
			var sri_document_info = sri_documents_info[i]
			this.sii_document_info_by_type[sri_document_info.document_class_id[0]] = sri_document_info;
			this.sii_document_info_by_sequence[sri_document_info.sequence_id[0]] = sri_document_info;
		}
	},
	get_ir_sequence_by_id : function(id) {
		return this.sequences_by_id[id];
	},
	get_sii_document_type_by_id : function(id) {
		return this.sii_document_type_by_id[id];
	},
	get_sii_document_type_by_type : function(document_type) {
		return this.sii_document_type_by_type[document_type];
	},
	get_sii_document_info_by_type : function(document_type) {
		return this.sii_document_info_by_type[document_type];
	},
	get_sii_document_info_by_sequence : function(sequence_id) {
		return this.sii_document_info_by_sequence[sequence_id];
	}
});
PosDBHistory.include({	
    _order_search_string: function(order){
        var str = order.name;
        if(order.sii_document_number){
            str += '|' + order.sii_document_number;
        }
        if(order.pos_reference){
            str += '|' + order.pos_reference;
        }
        if(order.pos_reprint_reference){
            str += '|' + order.pos_reprint_reference;
        }
        if(order.pos_reference_clean){
            str += '|' + order.pos_reference_clean;
        }
        if(order.partner_id){
            str += '|' + order.partner_id[1];
        }
        if(order.date_order){
            str += '|' + order.date_order;
        }
        if(order.user_id){
            str += '|' + order.user_id[1];
        }
        if(order.amount_total){
            str += '|' + order.amount_total;
        }
        if(order.state){
            str += '|' + order.state;
        }
        str = String(order.id) + ':' + str.replace(':','') + '\n';
        return str;
    }
}); 
});
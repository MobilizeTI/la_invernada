odoo.define('l10n_cl_pos_order_history_return.DB', function (require) {
"use strict";

var PosDB = require('point_of_sale.DB');

PosDB.include({	
	init : function(options) {
		options = options || {};
        var res = this._super(options);
		this.credit_note_reason_by_id = {};
		this.credit_note_reason_list = [];
		return res;
	},
	add_credit_note_reason: function(credit_note_reasons) {
		var self = this;
		self.credit_note_reason_list = credit_note_reasons;
		for (var i = 0, len = credit_note_reasons.length; i < len; i++) {
			var credit_note_reason = credit_note_reasons[i];
			self.credit_note_reason_by_id[credit_note_reason.id] = credit_note_reason;
		}
	},
	get_credit_note_reason_by_id : function(id) {
		return this.credit_note_reason_by_id[id] || {};
	},
	get_credit_note_reason_list : function() {
		return this.credit_note_reason_list || [];
	},
});
});
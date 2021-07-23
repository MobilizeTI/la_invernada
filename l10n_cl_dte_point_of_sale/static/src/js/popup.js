odoo.define('l10n_cl_dte_point_of_sale.popup', function (require) {
"use strict";

var screens = require('point_of_sale.screens');

var ButtonDocumentType = screens.ActionButtonWidget.extend({
	template : 'button_document_type',
	init: function (parent, options) {
        this._super(parent, options);
        this.pos.get('orders').bind('add remove change', function () {
            this.renderElement();
        }, this);
        this.pos.bind('change:selectedOrder', function () {
            this.renderElement();
        }, this);
    },
	button_click : function() {
		var self = this;
		var order = this.pos.get_order();
		if (order) {
			var document_sequences = self.pos.get_documents_type_for_selection();
			self.gui.show_popup('selection',{
                title: 'Seleccione Tipo de Documento',
                list: document_sequences,
                confirm: function (document_sequence) {
                    var order = self.pos.get_order();
                    order.set_document_sequence(document_sequence.id);
                }
            });
		}
	}
});

screens.define_action_button({
	'name' : 'button_document_type',
	'widget' : ButtonDocumentType,
	'condition' : function() {
		return this.pos.config.enable_change_document_type == true;
	}
});

return {
	ButtonDocumentType : ButtonDocumentType,
};
});



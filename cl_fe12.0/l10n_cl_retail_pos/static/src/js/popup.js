odoo.define('l10n_cl_retail_pos.popup', function (require) {
"use strict";

var core = require('web.core');
var gui = require('point_of_sale.gui');
var _t = core._t;

var PopupWidget = require('point_of_sale.popups');

var pos_picking = require('pos_create_stock.pos_picking');

var CreateGuiaDespachoPopupWidget = PopupWidget.extend({
    template: 'CreateGuiaDespachoPopupWidget',

    show: function(options){
        var self = this;
        options = options || {};
        self.picking_object = options.picking_object || false;
        self.partner_name = options.partner_name || "";
        this._super(options);
    },
    click_confirm: function(){
        var self = this;
        var move = true;
        var order = self.pos.get_order();
        var fields_warnings = self.validate_fields_aditional();
        if (fields_warnings.length > 0){
        	return;
        }
        if (self.picking_object){
        	var use_documents = $("#use_documents").prop("checked");
        	var picking_values = {
        		move_reason: "5", // traslados internos por defecto
        		use_documents: use_documents,
        	};
        	// solo si se va a hacer guia, pasar los datos
        	// caso contrario no pasar, par que tome los valores por defecto
        	if (use_documents){
        		picking_values = self.get_fields_aditional();
        	}
        	self.picking_object.create_stock_picking(picking_values);
        }
    },
    renderElement: function() {
        var self = this;
        this._super();
        $('#contact_id').select2();
        $('#vehicle').select2();
        $('#chofer').select2();
        $("#use_documents").on('change', function(){
			$("#container_guia").toggleClass("oe_hidden", !this.checked);
			$("#transport_type").toggleClass("detail-required", this.checked);
			$("#move_reason").toggleClass("detail-required", this.checked);
		});
        $("#transport_type").on('change', function(){
			$("#vehicle").toggleClass("detail-required", this.value === "2");
			$(".vehicle").toggleClass("oe_hidden", this.value !== "2");
			$("#chofer").toggleClass("detail-required", this.value === "2");
			$(".chofer").toggleClass("oe_hidden", this.value !== "2");
		});
        // provochar onchange inicial
        $("#transport_type").change();
    },
});

gui.define_popup({name:'create_guia_despacho_popup', widget: CreateGuiaDespachoPopupWidget});

pos_picking.PickingButton.include({
	button_click: function(){
        //  se reemplaza funcion para levantar un popup 
		// para preguntar datos para crear guia de despacho
		var self = this;
        var order = this.pos.get('selectedOrder');
        var currentOrderLines = order.get_orderlines();
        if(currentOrderLines.length <= 0){
        	self.gui.show_popup('error',{
                'title': _t('Create New Picking'),
                'body': _t('No hay lineas, por favor verifique!'),
            });
        	return;
        }
        else if(order.get_client() == null){
        	self.gui.show_popup('error',{
                'title': _t('Create New Picking'),
                'body': _t('Debe seleccionar el cliente!'),
            });
        	return;
        }
        else{
        	self.gui.show_popup('create_guia_despacho_popup', {
                picking_object: self,
                partner_name: order.get_client().name,
        	});
        }
    },
});

});
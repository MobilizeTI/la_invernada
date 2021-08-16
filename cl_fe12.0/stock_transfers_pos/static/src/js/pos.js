odoo.define('stock_transfers_pos.internal_transfers', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var rpc = require('web.rpc');
var core = require('web.core');
require('pos_longpolling.pos');
var models = require('point_of_sale.models');
var PopupWidget    = require('point_of_sale.popups');
var gui = require('point_of_sale.gui');
var _t = core._t;

models.load_models([{
    model:  'transfer.requisition',
    condition: function(self, temp){return self.config.allow_sent_internal_transfers},
    domain: function(self, temp){
    	return [['state','=','draft'], ['location_id','=', self.config.stock_location_id[0]]];
    },
    fields: ['name', 'location_id', 'location_dest_id'],
    loaded: function(self, internal_transfer_list){
        self.internal_transfer_list = internal_transfer_list;
        }
},{
    model:  'transfer.requisition',
    condition: function(self, temp){return self.config.allow_received_internal_transfers},
    domain: function(self, temp){
    	return [['state','=','approved'], ['location_dest_id','=', self.config.stock_location_id[0]]];
    },
    fields: ['name', 'location_id', 'location_dest_id'],
    loaded: function(self, internal_transfer_list){
        self.internal_transfer_list_to_received = internal_transfer_list;
    }
}]);

var _super_pos_model = models.PosModel.prototype;
models.PosModel = models.PosModel.extend({
    initialize: function () {
        _super_pos_model.initialize.apply(this, arguments);
        var self = this;
        this.ready.then(function () {
			self.bus.add_channel_callback("stock_transfers", self.on_stock_transfers_notify, self);
		});
    },
    on_stock_transfers_notify: function(message) {
        var self = this;
        var domain_to_approved = [['state','=','draft'], ['location_id','=', self.config.stock_location_id[0]]];
        var domain_to_receipt = [['state','=','approved'], ['location_dest_id','=', self.config.stock_location_id[0]]];
        self.get_stock_transfers(domain_to_approved).done(function(internal_transfer_list) {
            self.internal_transfer_list = internal_transfer_list;
        });
        self.get_stock_transfers(domain_to_receipt).done(function(internal_transfer_list) {
            self.internal_transfer_list_to_received = internal_transfer_list;
        });
    },
    get_stock_transfers: function (domain) {
    	var self = this;
        return rpc.query({
            model: 'transfer.requisition',
            method: 'search_read',
            args: [domain, ['name', 'location_id', 'location_dest_id']]
        });
    },
});

screens.ActionpadWidget.include({
	payment: function() {
		var self = this;
    	var order = self.pos.get_order();
    	if (order.GetSaleMode() === "internal_transfer_receive"){
    		self.gui.show_popup('error',{
                'title': _t('Transferencias Internas'),
                'body': _t('Esta en Modo Recepcion de transferencias, no puede realizar ventas, salga del modo de Recepcion Primero.'),
            });
    		return false;
    	}
    	return this._super();
    },
});

screens.OrderWidget.include({
	action_refresh_order_buttons : function(buttons, selected_order) {
		if (buttons.set_mode_internal_transfer_received) {
			if (selected_order.GetSaleMode() === "internal_transfer_receive") {
				buttons.set_mode_internal_transfer_received.highlight(true);
			} else {
				buttons.set_mode_internal_transfer_received.highlight(false);
			}
		}
		return this._super(buttons, selected_order);
	}
});

var InternalTransferPopupWidget = PopupWidget.extend({
    template: 'InternalTransferPopupWidget',
});
gui.define_popup({name:'internal_transfer', widget: InternalTransferPopupWidget});

var SelectionButtonPopupWidget = PopupWidget.extend({
    template: 'SelectionButtonPopupWidget',
    show: function(options){
        var self = this;
        options = options || {};
        this._super(options);
        this.item_selected = false;
        this.list = options.list || [];
        this.is_selected = options.is_selected || function (item) { return false; };
        this.renderElement();
    },
    click_item : function(event) {
        var $el = $(event.target);
        $el.parent().find('.selection-item').removeClass('selected');
        $el.addClass('selected');
    	var item = this.list[parseInt($el.data('item-index'))];
        item = item ? item.item : item;
        this.item_selected = item;
    },
    click_confirm: function(){
    	if (this.item_selected){
    		this.gui.close_popup();
            if (this.options.confirm) {
                this.options.confirm.call(this, this.item_selected);
            }
    	}
    },
});
gui.define_popup({name:'selection_button', widget: SelectionButtonPopupWidget});

 var InternalTransferCreateButton = screens.ActionButtonWidget.extend({
     template: 'InternalTransferCreateButton',
     button_click: function () {
         var self = this;
         var order = self.pos.get_order();
         var currentOrderLines = order.get_orderlines();
         if(currentOrderLines.length <= 0){
         	self.gui.show_popup('error',{
                 'title': _t('Transferencias internas'),
                 'body': _t('No hay lineas, por favor verifique!'),
             });
             return;
         }
         var selection_list = _.map(self.pos.internal_transfer_list, function (inventory) {
             return {
            	 label: _.str.sprintf('%(name)s(Origen: %(location)s. Destino: %(location_dest)s)',{
                 	name: inventory.name,
                 	location: inventory.location_id[1],
                 	location_dest: inventory.location_dest_id[1],
                 }),
                 item: inventory,
             };
         });
         self.gui.show_popup('selection_button',{
             title: _t('Seleccione Transferencia Interna a realizar'),
             list: selection_list,
             confirm: function (inventory) {
            	 self.gui.show_popup('confirm', {
                     title: _t('Transferencias internas'),
                     body: _t('¿Seguro de asignar las lineas a la Transferencia seleccionada?'),
                     confirm: function(){
                     	self.create_internal_transfer(inventory);
                     }
             	});
             }
         });
     },
     create_internal_transfer: function(inventory){
     	var self = this;
     	var order = self.pos.get_order();
     	var currentOrderLines = order.get_orderlines();
         var orderLines = [];
         for(var i=0; i<currentOrderLines.length;i++){
             orderLines.push(currentOrderLines[i].export_as_JSON());
         }
         rpc.query({
 			model:'transfer.requisition',
 			method:'set_internal_transfer_from_ui',
 			args: [inventory.id, orderLines]
         }).then(function(inventory_data){
             if(inventory_data){
                 while (order.get_orderlines().length) {
                     var line = order.get_orderlines()[0];
                     order.remove_orderline(line);
                 }
                 order.set_client();
                 order.trigger('change');
                 var line_index = _.findIndex(self.pos.internal_transfer_list, function (line) {
                     return line.id === inventory.id;
                 });
                 if (line_index  != -1){
                 	self.pos.internal_transfer_list.splice(line_index, 1);
                 }
                 var url = window.location.origin + _.str.sprintf("/web#id=%(id)s&view_type=form&model=%(model)s", inventory_data);
                 self.gui.show_popup('internal_transfer', {'url':url, 'name': inventory_data.name});
             }
         },function(err,event){
        	 event.preventDefault();
             if ((err.data || {}).message) {
 				self.gui.show_popup('error',{
 	                'title': _t('Error: Could not Save Changes'),
 	                'body': err.data.message,
 	            });
 			}
             else{
             	self.gui.show_popup('error',{
                     'title': _t('Error: Could not Save Changes'),
                     'body': _t('Your Internet connection is probably down.'),
                 });
             }
         });
     }
 });	
 
 var SetModeInternalTransferReceivedButton = screens.ActionButtonWidget.extend({
     template: 'SetModeInternalTransferReceivedButton',
     button_click: function () {
         var self = this;
         var order = self.pos.get_order();
         if (order.GetSaleMode() === "internal_transfer_receive"){
        	 self.gui.show_popup('confirm', {
                 title: _t('Transferencias internas'),
                 body: _t('¿Seguro de Salir del modo Recepcion de transferencias?, esto eliminara las lineas actuales'),
                 confirm: function(){
                	 order.SetSaleMode("");
                	 order.empty_cart();
                	 self.$el.removeClass('highlight');
                	 self.pos.gui.screen_instances.products.product_list_widget.renderElement();
                 }
         	});
         }else {
        	 order.SetSaleMode("internal_transfer_receive");
        	 this.$el.addClass('highlight');
        	 self.pos.gui.screen_instances.products.product_list_widget.renderElement();
         }
     },
 });
 
 var InternalTransferReceivedButton = screens.ActionButtonWidget.extend({
     template: 'InternalTransferReceivedButton',
     button_click: function () {
         var self = this;
         var order = self.pos.get_order();
         var currentOrderLines = order.get_orderlines();
         if(currentOrderLines.length <= 0){
         	self.gui.show_popup('error',{
                 'title': _t('Transferencias internas'),
                 'body': _t('No hay lineas, por favor verifique!'),
             });
             return;
         }
         var selection_list = _.map(self.pos.internal_transfer_list_to_received, function (inventory) {
             return {
            	 label: _.str.sprintf('%(name)s(Origen: %(location)s. Destino: %(location_dest)s)',{
                 	name: inventory.name,
                 	location: inventory.location_id[1],
                 	location_dest: inventory.location_dest_id[1],
                 }),
                 item: inventory,
             };
         });
         self.gui.show_popup('selection_button',{
             title: _t('Seleccione Transferencia Interna a Recibir'),
             list: selection_list,
             confirm: function (inventory) {
            	 self.gui.show_popup('confirm', {
                     title: _t('Transferencias internas'),
                     body: _t('¿Seguro de recibir los productos con las cantidades especificadas en la Transferencia seleccionada?'),
                     confirm: function(){
                     	self.received_internal_transfer(inventory);
                     }
             	});
             }
         });
     },
     received_internal_transfer: function(inventory){
     	var self = this;
     	var order = self.pos.get_order();
     	var currentOrderLines = order.get_orderlines();
         var orderLines = [];
         for(var i=0; i<currentOrderLines.length;i++){
             orderLines.push(currentOrderLines[i].export_as_JSON());
         }
         rpc.query({
 			model:'transfer.requisition',
 			method:'received_internal_transfer_from_ui',
 			args: [inventory.id, orderLines]
         }).then(function(inventory_data){
             if(inventory_data){
                 while (order.get_orderlines().length) {
                     var line = order.get_orderlines()[0];
                     order.remove_orderline(line);
                 }
                 order.set_client();
                 order.trigger('change');
                 var line_index = _.findIndex(self.pos.internal_transfer_list_to_received, function (line) {
                     return line.id === inventory.id;
                 });
                 if (line_index  != -1){
                 	self.pos.internal_transfer_list_to_received.splice(line_index, 1);
                 }
                 var url = window.location.origin + '/web#id=' + inventory_data[0] + '&view_type=form&model=transfer.requisition';
                 self.gui.show_popup('internal_transfer', {'url':url, 'name': inventory_data[1]});
             }
         },function(err,event){
             event.preventDefault();
             if ((err.data || {}).message) {
 				self.gui.show_popup('error',{
 	                'title': _t('Error: Could not Save Changes'),
 	                'body': err.data.message,
 	            });
 			}
             else{
             	self.gui.show_popup('error',{
                     'title': _t('Error: Could not Save Changes'),
                     'body': _t('Your Internet connection is probably down.'),
                 });
             }
         });
     }
 });

screens.define_action_button({
    'name': 'internal_transfer',
    'widget': InternalTransferCreateButton,
    'condition': function(){
        return (this.pos.config.allow_sent_internal_transfers);
    },
});

screens.define_action_button({
    'name': 'set_mode_internal_transfer_received',
    'widget': SetModeInternalTransferReceivedButton,
    'condition': function(){
        return (this.pos.config.allow_received_internal_transfers);
    },
});

screens.define_action_button({
    'name': 'internal_transfer_received',
    'widget': InternalTransferReceivedButton,
    'condition': function(){
        return (this.pos.config.allow_received_internal_transfers);
    },
});

return {
	InternalTransferPopupWidget: InternalTransferPopupWidget,
	InternalTransferCreateButton: InternalTransferCreateButton,
	SetModeInternalTransferReceivedButton: SetModeInternalTransferReceivedButton,
	InternalTransferReceivedButton: InternalTransferReceivedButton,
};
});


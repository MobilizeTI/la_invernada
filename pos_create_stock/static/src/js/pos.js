odoo.define('pos_create_stock.pos_picking', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var rpc = require('web.rpc');
var core = require('web.core');
var models = require('point_of_sale.models');
var PopupWidget    = require('point_of_sale.popups');
var gui = require('point_of_sale.gui');
var _t = core._t;

models.load_models([{
    model:  'stock.inventory',
    context: {inventory_from_pos: true},
    condition: function(self, temp){return self.config.allow_inventory_adjust},
    domain: function(self, temp){ 
    	return [['state','=','confirm'], ['filter','=','partial'], ['location_id','=', self.config.stock_location_id[0]]];
    },
    fields: ['name', 'location_id'],
    loaded: function(self, inventory_list){
        self.inventory_list = inventory_list;
        }
	}
]);

var _super_pos_model = models.PosModel.prototype;
models.PosModel = models.PosModel.extend({
    initialize: function () {
        _super_pos_model.initialize.apply(this, arguments);
        this.bus.add_channel_callback("stock_adjustment", this.on_inventory_adjustment_notify, this);
    },
    on_inventory_adjustment_notify: function(message) {
        var self = this;
        var domain_to_validate = [['state','=','confirm'], ['filter','=','partial'], ['location_id','=', self.config.stock_location_id[0]]];
        self.get_stock_adjustment(domain_to_validate).done(function(inventory_list) {
            self.inventory_list = inventory_list;
        });
    },
    get_stock_adjustment: function (domain) {
    	var self = this;
        return rpc.query({
            model: 'stock.inventory',
            method: 'search_read',
            args: [domain, ['name', 'location_id']]
        });
    },
});

var PickingPopupWidget = PopupWidget.extend({
    template: 'PickingPopupWidget',
});
gui.define_popup({name:'picking', widget: PickingPopupWidget});

var InventoryPopupWidget = PopupWidget.extend({
    template: 'InventoryPopupWidget',
});
gui.define_popup({name:'inventory', widget: InventoryPopupWidget});

var PickingButton = screens.ActionButtonWidget.extend({
    template: 'PickingButton',
    button_click: function(){
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
        	self.gui.show_popup('confirm', {
                title: _t('Create New Picking?'),
                body: _t('Si esta seguro, de clic en el boton Confirmar, caso contrario en el boton Cancelar'),
                confirm: function(){
                	self.create_stock_picking();
                }
        	});
        }
    },
    create_stock_picking: function(picking_values){
        var self = this;
        var order = this.pos.get('selectedOrder');
        var customer_id = order.get_client().id;
        var currentOrderLines = order.get_orderlines();
        var orderLines = [];
        for(var i=0; i<currentOrderLines.length;i++){
            orderLines.push(currentOrderLines[i].export_as_JSON());
        }
        rpc.query({
			model:'stock.picking',
			method:'create_picking_from_ui',
			args: [orderLines, customer_id, self.pos.config.id, picking_values]
        }).then(function(picking_data){
            if(picking_data){
                while (order.get_orderlines().length) {
                    var line = order.get_orderlines()[0];
                    order.remove_orderline(line);
                }
                order.set_client();
                var url = window.location.origin + '/web#id=' + picking_data[0] + '&view_type=form&model=stock.picking';
                self.gui.show_popup('picking', {'url':url, 'name':picking_data[1]});
            }
        }, function(err, event) {
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

var InventoryButton = screens.ActionButtonWidget.extend({
    template: 'InventoryButton',
    button_click: function(){
    	var self = this;
    	var order = self.pos.get_order();
        var currentOrderLines = order.get_orderlines();
        if(!order.inventory){
        	self.gui.show_popup('error',{
                'title': _t('Create New Inventory'),
                'body': _t('Debe seleccionar un inventario, por favor verifique!'),
            });
            return;
        }
        if(currentOrderLines.length <= 0){
        	self.gui.show_popup('error',{
                'title': _t('Create New Inventory'),
                'body': _t('No hay lineas, por favor verifique!'),
            });
            return;
        }
        self.gui.show_popup('confirm', {
            title: _t('Create New Inventory?'),
            body: _t('¿Seguro de asignar las lineas al inventario seleccionado?'),
            confirm: function(){
            	self.create_stock_inventory();
            }
    	});
    },
    create_stock_inventory: function(){
    	var self = this;
    	var order = self.pos.get_order();
    	var inventory_id = order.inventory.id;
    	var currentOrderLines = order.get_orderlines();
        var orderLines = [];
        for(var i=0; i<currentOrderLines.length;i++){
            orderLines.push(currentOrderLines[i].export_as_JSON());
        }
        rpc.query({
			model:'stock.inventory',
			method:'set_inventory_from_ui',
			args: [orderLines, inventory_id]
        }).then(function(inventory_data){
            if(inventory_data){
                while (order.get_orderlines().length) {
                    var line = order.get_orderlines()[0];
                    order.remove_orderline(line);
                }
                order.set_client();
                order.inventory = false;
                order.trigger('change');
                var line_index = _.findIndex(self.pos.inventory_list, function (line) {
                    return line.id === inventory_id;
                });
                if (line_index  != -1){
                	self.pos.inventory_list.splice(line_index, 1);
                }
                var url = window.location.origin + '/web#id=' + inventory_data[0] + '&view_type=form&model=stock.inventory';
                self.gui.show_popup('inventory', {'url':url, 'name':inventory_data[1]});
            }
        }, function(err, event) {
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

 var SelectionInventoryButton = screens.ActionButtonWidget.extend({
     template: 'SetInventory',
         init: function (parent, options) {
             this._super(parent, options);
             this.pos.get('orders').bind('add remove change', function () {
                 this.renderElement();
             }, this);
             this.pos.bind('change:selectedOrder', function () {
             this.renderElement();
         }, this);
     },
     button_click: function () {
         var self = this;
         var selection_list = _.map(self.pos.inventory_list, function (inventory) {
             return {
                 label: _.str.sprintf('%(name)s(%(location)s)',{
                 	name: inventory.name,
                 	location: inventory.location_id[1],
                 }),
                 item: inventory,
             };
         });
         self.gui.show_popup('selection',{
             title: _t('Seleccione Ajuste de inventario a validar'),
             list: selection_list,
             confirm: function (inventory) {
                 var order = self.pos.get_order();
                 order.inventory = inventory;
                 order.trigger('change');
             }
         });
     },
     get_current_inventory_name: function () {
         var name = _t('Sin Inventario');
         var order = this.pos.get_order();
         if (order) {
             if (order.inventory) {
            	 name  = _.str.sprintf('%(name)s(%(location)s)',{
            		 name: order.inventory.name,
            		 location: order.inventory.location_id[1],
            		 });
            }
         }
         return name;
     }
 });	 

screens.define_action_button({
    'name': 'picking',
    'widget': PickingButton,
    'condition': function(){
        return this.pos.config.allow_delivery_note;
    },
});

screens.define_action_button({
    'name': 'inventory',
    'widget': InventoryButton,
    'condition': function(){
        return this.pos.config.allow_inventory_adjust;
    },
});

screens.define_action_button({
    'name': 'set_inventory',
    'widget': SelectionInventoryButton,
    'condition': function(){
        return this.pos.config.allow_inventory_adjust;
    },
});

return {
	PickingPopupWidget: PickingPopupWidget,
	InventoryPopupWidget: InventoryPopupWidget,
	PickingButton: PickingButton,
	InventoryButton: InventoryButton,
	SelectionInventoryButton: SelectionInventoryButton,
};
});


/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('pos_speed_up.change_detector', function (require) {
"use strict";

var chrome = require('point_of_sale.chrome');
var rpc = require('web.rpc');

var screens = require('point_of_sale.screens');
var indexedDB = require('pos_speed_up.indexedDB');

if(!indexedDB){
    return;
}

var ChangeDetectorWidget = chrome.StatusWidget.extend({
    template: 'ChangeDetectorWidget',
    set_status: function (status, msg) {
        for (var i = 0; i < this.status.length; i++) {
            this.$('.jane_' + this.status[i]).addClass('oe_hidden');
        }
        this.$('.jane_' + status).removeClass('oe_hidden');
        if (msg) {
            this.$('.jane_msg').removeClass('oe_hidden').text(msg);
        } else {
            this.$('.jane_msg').addClass('oe_hidden').html('');
        }
    },
    start: function () {
        var self = this;
        self.count_sync = 0;
        this.pos.chrome.call('bus_service', 'onNotification', this, this.on_notification_callback);
        this.$el.click(function () {
            self.synch_without_reload(self);
        });
    },
    synch_without_reload: function () {
    	var self = this;
    	self.set_status('connecting');
        $.when(indexedDB.get('products'), indexedDB.get('customers')).then(function (products, customers) {
            // order_by product
            products = indexedDB.order_by(products, self.pos.get_model('product.product').order, 'esc');
            // add product
            self.pos.db.product_by_category_id = {};
            self.pos.db.category_search_string = {};
            products = self.pos.products_optimize.post_process_records(products);
            self.pos.products_optimize.original_loaded(self.pos, products);
            // add customer
            self.pos.db.partner_sorted = [];
            self.pos.db.partner_by_id = {};
            self.pos.db.partner_by_barcode = {};
            self.pos.customers_optimize.original_loaded(self.pos, customers);
            // re-render products
            var products_screen = self.pos.gui.screen_instances['products'];
            products_screen.product_list_widget = new screens.ProductListWidget(products_screen, {
                click_product_action: function (product) {
                    products_screen.click_product(product);
                },
                product_list: self.pos.db.get_product_by_category(0)
            });
            products_screen.product_list_widget.replace($('.product-list-container'));
            products_screen.product_categories_widget.product_list_widget = products_screen.product_list_widget;
         // re-render clients
            var client_screen = self.pos.gui.screen_instances['clientlist'];
            client_screen.partner_cache = new screens.DomCache();
            client_screen.render_list(self.pos.db.get_partners_sorted(1000));
            // -end-
            setTimeout(function () {
            	self.set_status('connected');
            }, 500);
            // reset count
            self.count_sync = 0;
        }).fail(function(){
        	self.set_status('disconnected', self.count_sync);
        });
    },
    on_notification_callback: function(notifications) {
    	var self = this;
        var data = notifications.filter(function (item) {
            return item[0][1] === 'change_detector';
        }).map(function (item) {
            return item[1];
        });
        var p = data.filter(function(item){
            return item.p;
        });
        var c = data.filter(function(item){
            return item.c;
        });
        self.on_change(p, c);
    },
    on_change: function (p, c) {
        var self = this;
    	if (p.length > 0) {
            this.sync_not_reload(self.pos.products_optimize, p.p).then(function (res){
            	self.synch_without_reload();	
            });
        }

        if (c.length > 0) {
        	this.sync_not_reload(self.pos.customers_optimize, c.c).then(function (res){
            	self.synch_without_reload();	
            });
        }
    },
    sync_not_reload: function (model_optimize, server_version) {
        var self = this;
        var def = new $.Deferred();
        var model = model_optimize.get_model();
        var client_version = self.call('local_storage', 'getItem', model_optimize.index_version);
        if (!/^\d+$/.test(client_version)) {
            client_version = 0;
        }
        if (client_version === server_version) {
            return;
        }
        rpc.query({
            model: model_optimize.table_name_backend,
            method: 'sync_not_reload',
            args: [client_version, model.fields]
        }).then(function (res) {
        	self.call('local_storage', 'setItem', model_optimize.index_version, res['latest_version']);
            // increase count
            self.count_sync += res['create'].length + res['delete'].length;
            if (self.count_sync > 0) {
                self.set_status('disconnected', self.count_sync);
            }
            indexedDB.get_object_store(model_optimize.table_name).then(function (store) {
                _.each(res['create'], function (record) {
                    store.put(record).onerror = function (e) {
                        console.log(e);
                        self.call('local_storage', 'setItem', model_optimize.index_version, client_version);
                    }
                });
                _.each(res['delete'], function (id) {
                    store.delete(id).onerror = function (e) {
                        console.log(e);
                        self.call('local_storage', 'setItem', model_optimize.index_version, client_version);
                    };
                });
                def.resolve();
            }).fail(function (error){
                console.log(error);
                self.call('local_storage', 'setItem', model_optimize.index_version, client_version);
                def.reject();
            });
        });
        return def;
    }
});

chrome.SynchNotificationWidget.include({
     renderElement: function(){
        new ChangeDetectorWidget(this, {}).appendTo('.pos-rightheader');
        this._super();
    }
});

});
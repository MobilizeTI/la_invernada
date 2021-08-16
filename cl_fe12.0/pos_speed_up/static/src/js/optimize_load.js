odoo.define('pos_speed_up.optimize_load', function (require) {
"use strict";

var Class = require('web.Class');
var rpc = require('web.rpc');
var mixins = require('web.mixins');
var ServicesMixin = require('web.ServicesMixin');

var indexedDB = require('pos_speed_up.indexedDB');
var models = require('point_of_sale.models');

if (!indexedDB) {
    return {OptimizeLoad: {}};
}

var OptimizeLoad = Class.extend(mixins.PropertiesMixin, ServicesMixin, {
	init: function(parent, options){
		mixins.PropertiesMixin.init.call(this);
		this.setParent(parent);
		this.pos = options.pos;
		this.model_name = options.model_name;
		this.default_order = options.default_order || [];
		this.table_name = options.table_name;
		this.table_name_backend = options.table_name_backend;
		this.index_version = options.table_name + "_index_version";
	},
	get_model: function () {
        var self = this;
		var _index = self.pos.models.map(function (e) {
            return e.model;
        }).indexOf(self.model_name);
        if (_index > -1) {
            return self.pos.models[_index]
        }
        return false;
    },
	init_load: function(){
		var self = this;
		var def = new $.Deferred();
        var model = this.get_model();
        if (!model) {
            def.reject();
        }
        if (indexedDB.is_cached(self.table_name)) {
            this.sync_data(model).then(function () {
                def.resolve();
            }).fail(function () {
                def.reject();
            });
        } else {
            this.save_data(model);
            def.resolve();
        }
        return def.promise();
	},
	sync_data: function (model) {
        var def = $.Deferred();
        var self = this;
        var client_version = self.call('local_storage', 'getItem', self.index_version);
        if (!/^\d+$/.test(client_version)) {
            client_version = 0;
        }
        rpc.query({
            model: self.table_name_backend,
            method: 'synchronize',
            args: [client_version]
        }).then(function (res) {
            // update version
        	self.call('local_storage', 'setItem', self.index_version, res['latest_version']);
            // create and delete
            var data_change = indexedDB.optimize_data_change(res['create'], res['delete'], res['disable']);
            model.domain.push(['id', 'in', data_change['create']]);
            self.original_loaded = model.loaded;
            model.loaded = function (self_pos, new_customers) {
                var done = new $.Deferred();
                indexedDB.get(self.table_name).then(function (records) {
                    records = records.concat(new_customers).filter(function (value) {
                        return data_change['delete'].indexOf(value.id) === -1;
                    });
                    // order_by
                    records = indexedDB.order_by(records, model.order || self.default_order, 'esc');
                    records = self.post_process_records(records);
                    self.original_loaded(self_pos, records);
                    done.resolve();
                }).fail(function (error) {
                    console.log(error);
                    self.call('local_storage', 'setItem', self.index_version, client_version);
                    done.reject();
                });
                // put and delete customer - indexedDB
                indexedDB.get_object_store(self.table_name).then(function (store) {
                    _.each(new_customers, function (customer) {
                        store.put(customer).onerror = function (ev) {
                            console.log(ev);
                            self.call('local_storage', 'setItem', self.index_version, client_version);
                        }
                    });
                    _.each(data_change['delete'], function (id) {
                        store.delete(id).onerror = function (ev) {
                            console.log(ev);
                            self.call('local_storage', 'setItem', self.index_version, client_version);
                        };
                    });
                }).fail(function (error) {
                    console.log(error);
                    self.call('local_storage', 'setItem', self.index_version, client_version);
                });
                return done;
            };
            def.resolve();
        }).fail(function (error) {
            console.log(error);
            def.reject();
        });
        return def.promise();
    },
    save_data: function (model) {
    	var self = this;
        this.original_loaded = model.loaded;
        model.loaded = function (self_pos, records) {
            indexedDB.save(self.table_name, records);
            records = indexedDB.order_by(records, model.order || self.default_order, 'esc');
            records = self.post_process_records(records);
            self.original_loaded(self_pos, records);
        };
        this.update_version_data();
    },
    update_version_data: function () {
    	var self = this;
        var old_version = self.call('local_storage', 'getItem', self.index_version);
        if (!/^\d+$/.test(old_version)) {
            old_version = 0;
        }
        rpc.query({
            model: self.table_name_backend,
            method: 'get_latest_version',
            args: [old_version]
        }).then(function (res) {
        	self.call('local_storage', 'setItem', self.index_version, res);
        });
    },
    post_process_records: function (records) {
    	return records;
    }
});

var ProductOptimizeLoad = OptimizeLoad.extend({
	post_process_records: function (records) {
		var self = this;
		var products = _.map(records, function (product) {
            product.categ = _.findWhere(self.pos.product_categories, {'id': product.categ_id[0]});
            return new models.Product({}, product);
        });
		return products;
    }
});

return {
	OptimizeLoad: OptimizeLoad,
	ProductOptimizeLoad: ProductOptimizeLoad,
};
});

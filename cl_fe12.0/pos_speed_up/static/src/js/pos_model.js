/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('pos_speed_up.pos_model', function (require) {
"use strict";
var models = require('point_of_sale.models');
var OptimizeLib = require('pos_speed_up.optimize_load');

var _super_pos = models.PosModel.prototype;

// for default sorted
models.load_fields('product.product', ['sequence', 'name']);
models.load_fields('res.partner', ['display_name']);

models.PosModel = models.PosModel.extend({
    initialize: function (session, attributes) {
        this.products_optimize = new OptimizeLib.ProductOptimizeLoad(attributes.chrome, {pos: this,
        	model_name: 'product.product', 
        	table_name: 'products',
        	table_name_backend: 'product.index',
        });
        this.customers_optimize = new OptimizeLib.OptimizeLoad(attributes.chrome, {pos: this,
        	model_name: 'res.partner',
        	default_order: ['display_name'],
        	table_name: 'customers',
        	table_name_backend: 'customer.index',
        });
        this.products_optimize.init_load();
        var wait = this.get_model('res.users');
        if (wait) {
            var _super_loaded = wait.loaded;
            wait.loaded = function (self, users) {
                var def = $.Deferred();
                _super_loaded(self, users);
                self.customers_optimize.init_load().always(function () {
                    def.resolve();
                });
                return def;
            };
        }
        _super_pos.initialize.call(this, session, attributes);
    },
    get_model: function (_name) {
        var _index = this.models.map(function (e) {
            return e.model;
        }).indexOf(_name);
        if (_index > -1) {
            return this.models[_index]
        }
        return false;
    },
});
});
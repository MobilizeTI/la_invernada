/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('pos_speed_up.indexedDB', function (require) {
    "use strict";

    var indexedDB = window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB || window.shimIndexedDB;

    if (!indexedDB) {
        window.alert("Your browser doesn't support a stable version of IndexedDB.")
    }

    var db_name = 'pos';
    var local_storage = require('web.local_storage');
    var exports = {
        get_object_store: function (_name) {
            var done = new $.Deferred();

            var request = indexedDB.open(db_name, 1);

            request.onerror = function (ev) {
                done.reject(ev);
            };

            request.onupgradeneeded = function (ev) {
                var db = ev.target.result;
                db.createObjectStore('customers', {keyPath: "id"});
                db.createObjectStore('products', {keyPath: "id"});
            };

            request.onsuccess = function (ev) {
                var db = ev.target.result;

                var transaction = db.transaction([_name], "readwrite");

                transaction.oncomplete = function () {
                    db.close();
                };

                if (!transaction) {
                    done.reject(new Error('Cannot create transaction with ' + _name));
                }

                var store = transaction.objectStore(_name);

                if (!store) {
                    done.reject(new Error('Cannot get object store with ' + _name));
                }

                done.resolve(store);
            };

            return done.promise();
        },
        save: function (_name, items) {
        	var self = this;
            $.when(this.get_object_store(_name))
                .done(function (store) {
                	local_storage.setItem(_name, 'cached');
                    _.each(items, function (item) {
                        store.put(item).onerror = function () {
                        	local_storage.setItem(_name, null);
                        }
                    });
                })
                .fail(function (error) {
                    console.log(error);
                });
        },
        is_cached: function (_name) {
        	return local_storage.getItem(_name) === 'cached';
        },
        get: function (_name) {
            var done = new $.Deferred();
            $.when(this.get_object_store(_name))
                .done(function (store) {
                    var request = store.getAll();

                    request.onsuccess = function (ev) {
                        var items = ev.target.result || [];
                        done.resolve(items);
                    };

                    request.onerror = function (error) {
                        done.reject(error);
                    };
                })
                .fail(function (error) {
                    done.reject(error);
                });
            return done.promise();
        },
        optimize_data_change: function (create_ids, delete_ids, disable_ids) {
            var new_create_ids = create_ids.filter(function (id) {
                return delete_ids.indexOf(id) === -1 && disable_ids.indexOf(id) === -1;
            });

            return {
                'create': new_create_ids,
                'delete': delete_ids.concat(disable_ids)
            }
        },
        order_by: function (objects, fields, type) {
            var self = this;
            if(!fields instanceof Array){
                fields = [fields];
            }
            if(fields.length <= 0 || (type !== 'esc' && type !== 'desc')){
                return objects;
            }
            var results = _.sortBy(objects, function (obj) {
                return self.get_compare(obj, fields);
            });
            switch (type){
                case 'esc':
                    return results;
                case 'desc':
                    return results.reverse();
            }
        },
        get_compare: function (obj, fields) {
             var exp = '';
            _.each(fields, function (field) {
                var value = obj[field] || String.fromCharCode(65500);
                exp += String(value);
            });
            return exp.toLowerCase();
        }
    };

    return exports;
});

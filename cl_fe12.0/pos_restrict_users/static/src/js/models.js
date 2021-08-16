odoo.define('pos_restrict_users.models', function (require) {
"use strict";

	var models = require('point_of_sale.models');

	var super_Model = models.PosModel.prototype;

	var pmodels = super_Model.models;
	var index = pmodels.length;
	for (var i = 0; i < pmodels.length; i++) {
		if (pmodels[i].model === "res.users" && _.contains(pmodels[i].fields, "pos_security_pin")){
			pmodels[i].domain = function(self){ return [['id', 'in', self.config.user_ids]]; };
			pmodels[i].loaded = function(self,users){ 
				// we attribute a role to the user, 'cashier' or 'manager', depending
	            // on the group the user belongs.
	            var pos_users = [];
	            var current_cashier = self.get_cashier();
	            for (var i = 0; i < users.length; i++) {
	                var user = users[i];
	                for (var j = 0; j < user.groups_id.length; j++) {
	                    var group_id = user.groups_id[j];
	                    if (group_id === self.config.group_pos_manager_id[0]) {
	                        user.role = 'manager';
	                        break;
	                    } else if (group_id === self.config.group_pos_user_id[0]) {
	                        user.role = 'cashier';
	                    }
	                }
	                if (! user.role) {
	                	user.role = 'cashier';
	                }
	                if (user.role) {
	                    pos_users.push(user);
	                }
	                // replace the current user with its updated version
	                if (user.id === self.user.id) {
	                    self.user = user;
	                }
	                if (user.id === current_cashier.id) {
	                    self.set_cashier(user);
	                }
	            }
	            self.users = pos_users;
	        };
			break;
		}
	}

});

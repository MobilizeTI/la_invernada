odoo.define('l10n_cl_retail_pos.models', function (require) {
"use strict";

var models = require('point_of_sale.models');

var models_dict = models.PosModel.prototype.models;
for (var i = 0; i < models_dict.length; i++) {
    var model = models_dict[i];
    if (model.model === 'product.product') {
        model.context = undefined;
    }
}

models.load_models({
	model: 'fleet.vehicle',
	fields: ['name',],
  	loaded: function(self, vehicles){
  		self.vehicles = vehicles;
  	},
});

var models_so = require('pos_create_so.pos_create_so');

var _super_ValidateClient = models_so.ValidateClient;

var ValidateClient = function(pos, client) {
	var res = _super_ValidateClient(pos, client);
	// cuando en la llamada super todo esta bien, validar los demas datos
	// pero si devuelve false es xq no paso la validacion, asi que no seguir validando
	if (res){
		if (!client.document_number){
			pos.gui.show_popup('error',{
				'title': 'Datos de Cliente Incompletos',
				'body':  'El Cliente seleccionado no tiene RUT, por favor verifique',
			});
			res = false;
		}
		if (!client.activity_description){
			pos.gui.show_popup('error',{
				'title': 'Datos de Cliente Incompletos',
				'body':  'El Cliente seleccionado no tiene Giro, por favor verifique',
			});
			res = false;
		}
	}
	return res;
};

models_so.ValidateClient = ValidateClient;

});
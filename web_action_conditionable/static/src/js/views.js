odoo.define('web.web_action_conditionable', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');
    require('web.EditableListRenderer');

    ListRenderer.include({
    	init: function (parent, state, params) {
			var arch = params.arch;
			if (arch) {
				if (arch.attrs.create_conditionable){
					var expr = arch.attrs.create_conditionable;
					var expression = py.parse(py.tokenize(expr));
					var result = py.evaluate(expression, parent.record.evalContext).toJSON();
					params.addCreateLine = result;
				}
				if (arch.attrs.delete_conditionable){
					var expr = arch.attrs.delete_conditionable;
					var expression = py.parse(py.tokenize(expr));
					var result = py.evaluate(expression, parent.record.evalContext).toJSON();
					params.addTrashIcon = result;
				}
			}
			return this._super.apply(this, arguments);
    	}
    });
});

odoo.define('dimabe_manufacturing.in_screen', function (require) {
    'use strict';
    var form_widget = require('web.form_widgets');
    var core = require('web.core');
    var _t = core._t;
    var Qweb = core.Qweb;

    form_widget.WidgetButton.include({
        onkeypress : function (e) {
            if(e.keyCode == 13){
                console.log("Hola");
            }
        }
    })
})
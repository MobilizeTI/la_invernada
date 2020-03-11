odoo.define('dimabe_manufacturing.stock_production_lot', function (require) {
    var core = require('web.core');
    var FormRenderer = require('web.FormRenderer');
    document.addEventListener("keydown",function (event) {
        if (event.code == 'Enter')
            console.log(FormRenderer)
    })

})
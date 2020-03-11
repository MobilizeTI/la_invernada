odoo.define('dimabe_manufacturing.stock_production_lot', function (require) {
    var core = require('web.core');
    var field = new odoo.Model('stock.production.lot')
    field.query(['name'])
    document.addEventListener("keydown",function (event) {
        if (event.code == 'Enter')
            console.log(field)
    })

})
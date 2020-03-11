odoo.define('dimabe_manufacturing', function (require) {
    var model = require('web.Model');
    var Lot = new Model('stock.production.lot');
    document.addEventListener("keydown",function (event) {
        if (event.code == 'Enter')
            console.log(Lot)

    })

})
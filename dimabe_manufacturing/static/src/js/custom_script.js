odoo.define('stock.production.lot', function (require) {
    'use strict';
    $(document).ready(function () {
        $(document).onkeydown(function (e) {
            if(e.keyCode == 13){
                if($('button:contains("Guardar")')){
                    $('button:contains("Guardar")').click();
                }
            }
        })
    })
})
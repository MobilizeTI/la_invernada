var AbstractField = require('web.AbstractField');
var core = require(web.core);
var field_registry = require('web.field_registry');
var time = require('web.time');

var _t = core._t;

var TimeCounter = AbstractField.extend({
    supportedFieldTypes: [],
    @override
    willStart: function () {
        var self = this;
        var def = this._rpc({
            model: 'stock.picking',
            method: "",
            domain: [
                [
                    'stock_picking_id', '=', this.record.data.id
                ],
                [
                    'user_id', this.getSession().uid
                ],
            ]
        }).then(function(result){
           if(self.mode === 'readonly'){
               var currentDate = new Date();
               self.elapsed_time = 0;
               _.each
           }
        });
    }
})
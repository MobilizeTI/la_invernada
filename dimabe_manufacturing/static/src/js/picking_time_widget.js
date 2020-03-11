import {toDateFormat} from "./date_methods";

odoo.define('dimabe_manufacturing.picking_integer_time', function (require) {
    'use strict';
    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var timeField = AbstractField.extend({
        supportedFieldTypes: ['integer'],
        _render: function () {
            this._timeCounter()
        },
        destroy: function () {
            this._super.apply(this, arguments);
            clearTimeout(this.timer);
        },
        _timeCounter: function () {
            var self = this;
            clearTimeout(this.timer);
            var toSum = 0
            if (this.record.data.unpelled_state === 'drying') {
                this.timer = setTimeout(function () {
                    var currentDate = new Date().getTime() / 1000
                    toSum = parseInt(currentDate - self.record.data.init_active_time)
                    self.$el.context.classList.remove('o_field_empty')
                    self.$el.html($('<span>' + self._to_date_format((self.record.data.drier_counter + toSum)) + '</span>', {
                        'class': 'success'
                    }));
                    self._timeCounter();
                }, 1000);
            }else{
                clearTimeout(this.timer)
                this.$el.html($('<span>' + this._to_date_format(self.record.data.drier_counter) + '</span>'))
            }
        },
        _to_date_format: toDateFormat(),
    })

    fieldRegistry.add('picking_time_live', timeField);
});

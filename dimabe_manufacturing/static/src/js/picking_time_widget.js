odoo.define('dimabe_manufacturing.picking_integer_time', function (require) {
    'use strict';
    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var date_helper = require('dimabe_manufacturing.date_helper')
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
            console.log(this.record.data.unpelled_state, this.record.data.oven_time_is_running)
            if (this.record.data.unpelled_state === 'drying' || this.record.data.oven_time_is_running) {
                this.timer = setTimeout(function () {
                    var currentDate = new Date().getTime() / 1000
                    toSum = parseInt(currentDate - self.record.data.oven_init_active_time)
                    self.$el.context.classList.remove('o_field_empty')
                    self.$el.html($('<span>' + self._to_date_format((self.record.data.drier_counter + toSum)) + '</span>', {
                        'class': 'success'
                    }));
                    self._timeCounter();
                }, 1000);
            } else {
                clearTimeout(this.timer)
                this.$el.html($('<span>' + this._to_date_format(self.record.data.drier_counter) + '</span>'))
            }
        },
        _to_date_format: date_helper.toDateFormat,
    })

    fieldRegistry.add('picking_time_live', timeField);
});

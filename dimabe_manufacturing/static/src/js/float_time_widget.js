

odoo.define('dimabe_manufacturing.integer_time', function (require) {
    'use strict';
    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var toDateFormat = require('dimabe_manufacturing.date_helper')

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
            if (this.record.data.init_active_time && !this.record.data.finish_active_time) {
                this.timer = setTimeout(function () {
                    var currentDate = new Date().getTime() / 1000
                    toSum = parseInt(currentDate - self.record.data.init_active_time)
                    self.$el.context.classList.remove('o_field_empty')
                    self.$el.html($('<span>' + self._to_date_format((self.record.data.active_seconds + toSum)) + '</span>', {
                        'class': 'success'
                    }));
                    self._timeCounter();
                }, 1000);
            }else{
                clearTimeout(this.timer)
                this.$el.html($('<span>' + this._to_date_format(self.record.data.active_seconds) + '</span>'))
            }
        },
        _to_date_format: toDateFormat, //function (seconds) {
        //     var days = parseInt((seconds / 86400).toString())
        //     var hours = 0
        //     var minutes = 0
        //     var sec = 0
        //     if (seconds % 86400 > 0) {
        //         hours = parseInt(((seconds % 86400) / 3600).toString())
        //         if ((seconds % 86400) % 3600 > 0) {
        //             minutes = parseInt((((seconds % 86400) % 3600) / 60).toString())
        //             if (((seconds % 86400) % 3600) % 60 > 0)
        //                 sec = parseInt((((seconds % 86400) % 3600) % 60).toString())
        //         }
        //
        //     }
        //     return `${this._normalize_number(days)}(d) ${this._normalize_number(hours)}:${this._normalize_number(minutes)}:${this._normalize_number(sec)}`
        //
        // },
        // _normalize_number: function (number) {
        //     var tmp = '0' + number
        //     tmp = tmp.substr(tmp.length - 2, 2)
        //     return tmp
        // }
    })

    fieldRegistry.add('time_live', timeField);
});

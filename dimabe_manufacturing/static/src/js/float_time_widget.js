odoo.define('dimabe_manufacturing.integer_time', function (require) {
    'use strict';
    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var timeField = AbstractField.extend({
        supportedFieldTypes: ['integer'],
        _render: function () {
            this.$el.context.classList.remove('o_field_empty')
            this._timeCounter()
        },
        _timeCounter: function () {
            var self = this;
            clearTimeout(this.timer);
            this.timer = setTimeout(function () {
                self.record.data.active_seconds += 1
                self._timeCounter();
            }, 1000);

            this.$el.html($('<span>' + self._to_date_format(self.record.data.active_seconds) + '</span>', {
                'class': 'success'
            }));
        },
        _to_date_format: function (seconds) {
            var days = parseInt((seconds / 86400).toString())
            var hours = 0
            var minutes = 0
            var sec = 0
            if (seconds % 86400 > 0) {
                hours = parseInt(((seconds % 86400) / 3600).toString())
                if ((seconds % 86400) % 3600 > 0) {
                    minutes = parseInt((((seconds % 86400) % 3600) / 60).toString())
                    if (((seconds % 86400) % 3600) % 60 > 0)
                        sec = parseInt((((seconds % 86400) % 3600) % 60).toString())
                }

            }
            return `${this._normalize_number(days)} ${this._normalize_number(hours)}:${this._normalize_number(minutes)}:${this._normalize_number(sec)}`

        },
        _normalize_number: function (number) {
            var tmp = `0${number}`
            tmp = tmp.substr(tmp.length - 2, 2)
            console.log(tmp)
            return tmp
        }
    })

    fieldRegistry.add('time_live', timeField);
});


// var TimeCounter = AbstractField.extend({
//     supportedFieldTypes: [],
//     /**
//      * @override
//      */
//     willStart: function () {
//         var self = this;
//         var def = this._rpc({
//             model: 'mrp.workcenter.productivity',
//             method: 'search_read',
//             domain: [
//                 ['workorder_id', '=', this.record.data.id],
//                 ['user_id', '=', this.getSession().uid],
//             ],
//         }).then(function (result) {
//             if (self.mode === 'readonly') {
//                 var currentDate = new Date();
//                 self.duration = 0;
//                 _.each(result, function (data) {
//                     self.duration += data.date_end ?
//                         self._getDateDifference(data.date_start, data.date_end) :
//                         self._getDateDifference(time.auto_str_to_date(data.date_start), currentDate);
//                 });
//             }
//         });
//         return $.when(this._super.apply(this, arguments), def);
//     },
//
//     destroy: function () {
//         this._super.apply(this, arguments);
//         clearTimeout(this.timer);
//     },
//
//     //--------------------------------------------------------------------------
//     // Public
//     //--------------------------------------------------------------------------
//
//     /**
//      * @override
//      */
//     isSet: function () {
//         return true;
//     },
//
//     //--------------------------------------------------------------------------
//     // Private
//     //--------------------------------------------------------------------------
//
//     /**
//      * Compute the difference between two dates.
//      *
//      * @private
//      * @param {string} dateStart
//      * @param {string} dateEnd
//      * @returns {integer} the difference in millisecond
//      */
//     _getDateDifference: function (dateStart, dateEnd) {
//         return moment(dateEnd).diff(moment(dateStart));
//     },
//     /**
//      * @override
//      */
//     _render: function () {
//         this._startTimeCounter();
//     },
//     /**
//      * @private
//      */
//     _startTimeCounter: function () {
//         var self = this;
//         clearTimeout(this.timer);
//         if (this.record.data.is_user_working) {
//             this.timer = setTimeout(function () {
//                 self.duration += 1000;
//                 self._startTimeCounter();
//             }, 1000);
//         } else {
//             clearTimeout(this.timer);
//         }
//         this.$el.html($('<span>' + moment.utc(this.duration).format("HH:mm:ss") + '</span>'));
//     },
// });



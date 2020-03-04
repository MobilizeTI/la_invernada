odoo.define('dimabe_manufacturing.validate_on_scanned', function (require) {
    'use strict';
    let AbstractField = require('web.AbstractField');
    let fieldRegistry = require('web.field_registry');
    let timeField = AbstractField.extend({
        supportedFieldTypes: ['integer'],
        init: function () {

        }
    })

    field_registry.add('time_live', timeField);
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



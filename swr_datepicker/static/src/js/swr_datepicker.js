odoo.define('swr.web.datepicker', function (require) {
"use strict";

var core = require('web.core');
var DatePicker = require('web.datepicker');
var field_utils = require('web.field_utils');
var time = require('web.time');

var _t = core._t;

var formatDateOrigin = field_utils.format.date;
var parseDateOrigin = field_utils.parse.date;
var getLangDateFormatOrigin = time.getLangDateFormat;

time.getLangDateFormat = function (viewMode) {
	if (viewMode){
		// return format according viewMode
		var l10n = _t.database.parameters;
		return time.strftime_to_moment_format(viewMode === "months" ? l10n.month_format : l10n.year_format)
	}
	return this.strftime_to_moment_format(_t.database.parameters.date_format);
}

field_utils.format.date = function (value, field, options) {
	var viewMode = ((options || {}).viewMode) || (((options || {}).datepicker || {}).viewMode);
	if (viewMode && value){
		var date_format = time.getLangDateFormat(viewMode);
	    return value.format(date_format);
	} else{
		return formatDateOrigin(value, field, options);
	}
}

field_utils.parse.date = function (value, field, options) {
	if ((options || {}).viewMode && value){
		var datePattern = time.getLangDateFormat(options.viewMode);
		var datePatternWoZero = datePattern.replace('MM','M').replace('DD','D');
	    var date;
	    if (options && options.isUTC) {
	        date = moment.utc(value);
	    } else {
	        date = moment.utc(value, [datePattern, datePatternWoZero, moment.ISO_8601], true);
	    }
	    if (date.isValid()) {
	        if (date.year() === 0) {
	            date.year(moment.utc().year());
	        }
	        if (date.year() >= 1900) {
	            date.toJSON = function () {
	                return this.clone().locale('en').format('YYYY-MM-DD');
	            };
	            return date;
	        }
	    }
	    throw new Error(_.str.sprintf(core._t("'%s' is not a correct date"), value));
	} else{
		return parseDateOrigin(value, field, options);
	}
}

DatePicker.DateWidget.include({
	init: function (parent, options) {
        if (options && (options.viewMode==="months" || options.viewMode==="years")) {
        	var _options = {};
            var l10n = _t.database.parameters;
            // pass format if viewMode is Set
            _options.format = time.strftime_to_moment_format((options.viewMode==="months")? l10n.month_format : l10n.year_format);
            options = _.defaults(_options || {}, options);
        }
        this._super(parent, options);
    },
    // replace functions for add this.options
    _formatClient: function(v) {
    	return field_utils.format[this.type_of_date](v, null, _.extend(this.options, {timezone: false}));
    },
    _parseClient: function(v) {
    	return field_utils.parse[this.type_of_date](v, null, _.extend(this.options, {timezone: false}));
    }
});

return DatePicker;
})

odoo.define('dimabe_manufacturing.date_helper', function (require) {
    'use strict'
    var toDateFormat = function (seconds) {
        var minutes = 0
        var sec = 0
        var hours = parseInt((seconds / 3600).toString())
        if (seconds % 3600 > 0) {
            minutes = parseInt(((seconds % 3600) / 60).toString())
            if ((seconds % 3600) % 60 > 0)
                sec = parseInt(((seconds % 3600) % 60).toString())
        }

        return `${normalizeNumber(hours)}:${normalizeNumber(minutes)}:${normalizeNumber(sec)}`
    }

    var normalizeNumber = function (number) {
        var tmp = '0' + number
        tmp = tmp.substr(tmp.length - 2, 2)
        return tmp
    }

    return {normalizeNumber, toDateFormat}
})
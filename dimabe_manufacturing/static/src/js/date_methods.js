function toDateFormat(seconds) {
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
    return `${normalizeNumber(days)}(d) ${normalizeNumber(hours)}:${normalizeNumber(minutes)}:${normalizeNumber(sec)}`
}

function normalizeNumber(number) {
    var tmp = '0' + number
    tmp = tmp.substr(tmp.length - 2, 2)
    return tmp
}

export {normalizeNumber, toDateFormat}
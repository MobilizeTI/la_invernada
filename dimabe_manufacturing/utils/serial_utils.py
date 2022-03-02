def get_zeros(counter):
    if 1 <= counter <= 9:
        return '00'
    elif 10 <= counter <= 99:
        return '0'
    else:
        return ''


def remove_zeros(number):
    for item in number:
        if int(item) > 0 or not item:
            index = number.index(item)
            return number[index:]
        continue

def int_to_time(integer_number):
    days = int(integer_number / 86400)
    hours = 0
    minutes = 0
    sec = 0
    if integer_number % 86400 > 0:
        hours = int((integer_number % 86400) / 3600)
        if (integer_number % 86400) % 3600 > 0:
            minutes = int(((integer_number % 86400) % 3600) / 60)
            if ((integer_number % 86400) % 3600) % 60 > 0:
                sec = int(((integer_number % 86400) % 3600) % 60)

    return '{} {}:{}:{}'.format(
        '0{}'.format(days)[-2:],
        '0{}'.format(hours)[-2:],
        '0{}'.format(minutes)[-2:],
        '0{}'.format(sec)[-2:]
    )

from odoo import models
import re


def format_rut(rut_str):
    rut_str = clean_rut(rut_str)
    dv = rut_str[-1:]
    rut_body = rut_str[:-1]
    counter = 0
    formatted_body = ''
    for character in rut_body[::-1]:
        formatted_body += character
        counter += 1
        if counter == 3 and len(formatted_body.replace('.', '')) < len(rut_body):
            counter = 0
            formatted_body += '.'
    return '{}-{}'.format(formatted_body[::-1], dv)


def clean_rut(rut_str):
    dv = str.upper(rut_str[-1:])
    rut_str = rut_str[0:-1]
    pattern = r'\D'
    res = re.sub(pattern, '', rut_str)
    return '{}{}'.format(res, dv)


def validate_rut(rut_str):
    rut_str = clean_rut(rut_str)
    dv = rut_str[-1:]
    rut_str = rut_str[0:-1]
    carry = 2
    tmp_res = 0
    for x in rut_str[::-1]:
        tmp_res += int(x) * carry
        if carry == 7:
            carry = 1
        carry += 1
    mod = tmp_res % 11
    res = 11 - mod
    if res == 11:
        digit = '0'
    elif res == 10:
        digit = "k"
    else:
        digit = str(res)
    return str(digit).lower() == str(dv).lower()


def prepare_rut(values):
    if 'invoice_rut' in values and values['invoice_rut']:
        if not validate_rut(values['invoice_rut']):
            raise models.ValidationError('el rut no es válido')
        values['invoice_rut'] = format_rut(values['invoice_rut'])

from django import template
from decimal import Decimal


register = template.Library()


@register.filter
def get_session_dict_value(dictionary, key):
    if key in dictionary:
        if type(key) != str:
            key = str(key)
        return dictionary[key]

@register.filter
def get_phone_format_string(value):
    if type(value) in [int, float, Decimal]:
        value = str(value)
    if type(value) == str:
        return '%s-%s-%s-%s' % (value[0:3], value[3:6], value[6:8], value[8:10])

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def russian_price(context, product):
    def format_sting(price):
        return '{0:,}'.format(int(price)).replace(',', ' ')

    user = context['user']

    if 'buyer_type' in dir(user):
        for price in product.price_set.all():
            if price.buyer_type == user.buyer_type and price.value > 0:
                return format_sting(price.value)

    if product.base_price > 0:
        return format_sting(product.base_price)
    else:
        return ''


@register.filter
def get_session_dict_value(dictionary, key):
    if key in dictionary:
        if type(key) != str:
            key = str(key)
        return dictionary[key]

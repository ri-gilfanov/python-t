from django.conf.urls import url
from .views import (
    get_catalog,
    get_category,
    get_product,
    parse_xml,
    get_cart,
    request_to_cart,
    print_products,
)


urlpatterns = [
    url(r'^catalog/$', get_catalog, name='catalog'),
    url(r'^category_(?P<pk>\d+)/(?:page_(?P<page_number>\d+)/)?$', get_category, name='category'),
    url(r'^product_(?P<pk>\d+)/$', get_product, name='product'),
    url(r'^cart/$', get_cart, name='cart'),
    url(r'^xml/$', parse_xml),
    url(r'^request_to_cart/$', request_to_cart, name='request_to_cart'),
    url(r'^print_products/$', print_products),
]

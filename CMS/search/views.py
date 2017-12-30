from django.shortcuts import render
from shop.models import Product
from core.view_functions import get_extend_paginator
from django.contrib.postgres.search import SearchVector, SearchQuery


def get_common_search(request, page_number=None):
    context = {}
    if 'search' in request.GET:
        search = request.GET['search']
        products = Product.objects.annotate(search=SearchVector('name', 'vendor_code', config='russian'))
        products = products.filter(search=SearchQuery(search, config='russian'))
        #products = products[:5]
        obj_list = products.prefetch_related('photo_set', 'category', 'price_set__buyer_type', 'price_set__product')
        get_extend_paginator(context, obj_list, page_number, per_page=24)
        context['products'] = obj_list
        context['url_paginator_page'] = 'common_search'
        context['search_query'] = search
    return render(request, 'search/search__common.html', context)

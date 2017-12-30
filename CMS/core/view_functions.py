from django.core.paginator import Paginator


def get_extend_paginator(context, obj_list, page_number, per_page=50):
    if page_number is None:
        page_number = 1
    paginator = Paginator(object_list=obj_list, per_page=per_page)
    page_number = int(page_number)
    full_slice = 9
    half_slice = full_slice // 2
    if page_number <= half_slice:
        context['paginator_start'] = 0
        context['paginator_end'] = full_slice + 1
    elif (
        page_number >= half_slice - 1
        and page_number <= paginator.num_pages - half_slice
    ):
        context['paginator_start'] = page_number - half_slice - 1
        context['paginator_end'] = page_number + half_slice + 1
    else:
        context['paginator_start'] = paginator.num_pages - full_slice
        context['paginator_end'] = paginator.num_pages + 1
    context['paginator_start_link'] = half_slice + 1
    context['paginator_end_link'] = paginator.num_pages - half_slice
    context['paginator_range'] = paginator.page_range
    context['paginator_page'] = paginator.page(number=page_number)

from django.shortcuts import render
from django.http import HttpResponse
from shop.xml_parser import XMLProductBrander


def main_page(request):
    context = {}
    return render(request, 'core/main_page.html', context)


def c7e4d6997981(request):
    return HttpResponse('c9be80c253a1')

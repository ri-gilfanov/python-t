from django.shortcuts import render
from .models import CustomPage


def get_custom_page(request, pk):
    context = {}
    context['obj'] = CustomPage.objects.get(pk=pk)
    return render(request, 'pages/custom_page.html', context)

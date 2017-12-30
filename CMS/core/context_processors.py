from django.conf import settings


def site_info(request):
    context = {
        'site_name': settings.SITE_NAME,
        'site_description': settings.SITE_DESCRIPTION,
    }
    return context

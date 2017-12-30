from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
import os


urlpatterns = [
    url(r'^', include('users.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^', include('core.urls')),
    url(r'^', include('shop.urls')),
    url(r'^', include('search.urls')),
    url(r'^', include('pages.urls')),
]


if settings.DEBUG and os.uname().nodename != 'pharmacosphere':
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

urlpatterns.extend(
    static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
)


urlpatterns.extend(
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
)

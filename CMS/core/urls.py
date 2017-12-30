from django.conf.urls import url
from .views import (
    main_page,
    c7e4d6997981,
)


urlpatterns = [
    url(r'^$', main_page, name='main_page'),
    url(r'^c7e4d6997981.html$', c7e4d6997981),
]

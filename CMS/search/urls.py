from django.conf.urls import url
from .views import (
    get_common_search,
)


urlpatterns = [
    url(r'^search/(?:page_(?P<page_number>\d+)/)?$', get_common_search, name='common_search'),
]

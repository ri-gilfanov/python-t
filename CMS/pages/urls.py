from django.conf.urls import url
from .views import (
    get_custom_page,
)


urlpatterns = [
     url(r'^page_(?P<pk>\d+)/$', get_custom_page, name='custom_page'),
]

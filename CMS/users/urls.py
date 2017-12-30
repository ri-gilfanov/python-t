from django.conf.urls import include, url
from .views import (
    sign_in, sign_out, sign_up,
    get_profile, get_profile_editing, get_legal_entities_editing,
    get_profile_buyer_receipts, get_profile_buyer_receipt,
)


urlpatterns = [
    url(r'^sign_in/$', sign_in, name='sign_in'),
    url(r'^sign_out/$', sign_out, name='sign_out'),
    url(r'^sign_up/$', sign_up, name='sign_up'),
    url(r'^profile/$', get_profile, name='profile'),
    url(r'^profile/editing/$', get_profile_editing, name='profile_editing'),
    url(r'^profile/buyer_receipts/$', get_profile_buyer_receipts, name='buyer_receipts'),
    url(r'^profile/buyer_receipt_(?P<pk>\d+)/$', get_profile_buyer_receipt, name='buyer_receipt'),
    url(r'^profile/legal_entities/$', get_legal_entities_editing, name='legal_entities'),
]

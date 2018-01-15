from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.urls import reverse_lazy
from django.http import QueryDict

from rest_framework.urlpatterns import format_suffix_patterns
from django_cas_ng.views import login as cas_login, logout as cas_logout, callback as cas_callback

from imageledger.views import search_views, api_views, list_views, favorite_views, tag_views, site_views
from imageledger.forms import FIELD_DEFAULT

class MetRedirectView(RedirectView):
    permanent = True
    query_string = True
    pattern_name = 'search-met'

    def get_redirect_url(self, *args, **kwargs):
        url = reverse_lazy('index') + '?'
        qd = QueryDict('', mutable=True, )
        qd.update({'providers': 'met'})
        qd.setlistdefault('search_fields', FIELD_DEFAULT)
        url += qd.urlencode()
        return url

urlpatterns = [
    # Custom search URLs
    path('themet', MetRedirectView.as_view(), name='search-met'),

    path('', search_views.index, name='index'),
    path('image/detail', search_views.by_image, name="by-image"),
    re_path('image/detail/(?P<identifier>.*)', search_views.detail, name="detail"),

    # CAS
    path('accounts/login', cas_login, name='cas_ng_login'),
    path('accounts/logout', cas_logout, name='cas_ng_logout'),
    path('accounts/callback', cas_callback, name='cas_ng_proxy_callback'),

    # Other auth-related pages
    path('accounts/profile', site_views.profile, name="profile"),
    path('accounts/delete', site_views.delete_account, name="delete-account"),

    # Lists (public)
    path('list/<slug:slug>/', list_views.OLListDetail.as_view(), name='list-detail'),

    # Lists (user admin)
    path('list/add/', list_views.OLListCreate.as_view(), name='my-list-add'),
    path('list/mine/<slug:slug>/', list_views.OLListUpdate.as_view(), name='my-list-update'),
    path('list/mine/<slug:slug>/delete', list_views.OLListDelete.as_view(), name='my-list-delete'),
    path('lists/mine', list_views.OLOwnedListList.as_view(), name="my-lists"),

    # Favorites
    path('favorites/mine', favorite_views.FavoriteList.as_view(), name='my-favorites'),

    # User tags
    path('tags/mine', tag_views.UserTagsList.as_view(), name='my-tags'),
    path('tags/mine/<slug:slug>/', tag_views.UserTagsDetail.as_view(), name='my-tags-detail'),

    # About and other static pages
    path('about', site_views.about, name='about'),
    path('health', site_views.health, name='health'),
    path('robots.txt', site_views.robots, name='robots'),

]

apipatterns = [
    # List API
    path('api/v1/lists', api_views.ListList.as_view()),
    path('api/v1/autocomplete/lists', api_views.ListAutocomplete.as_view()),
    path('api/v1/lists/<slug:slug>', api_views.ListDetail.as_view()),

    # Favorite API
    path('api/v1/images/favorite/<str:identifier>', api_views.FavoriteDetail.as_view()),
    path('api/v1/images/favorites', api_views.FavoriteList.as_view()),

    # User Tags API
    path('api/v1/images/tags', api_views.UserTagDetail.as_view()),
    path('api/v1/images/tags/<str:identifier>/<str:tag>', api_views.UserTagDetail.as_view()),
    path('api/v1/images/tags/<str:identifier>', api_views.UserTagsList.as_view()),
    path('api/v1/autocomplete/tags', api_views.UserTagsAutocomplete.as_view()),

]


apipatterns = format_suffix_patterns(apipatterns)

urlpatterns += apipatterns

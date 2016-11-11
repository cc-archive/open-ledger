from django.conf.urls import url, include

from imageledger.views import search_views

urlpatterns = [
    url(r'^$', search_views.index, name='index'),
    url(r'^provider-apis$', search_views.provider_apis, name='provider-apis'),
    url(r'^provider/(?P<provider>\w+)$', search_views.by_provider, name='by-provider'),
    url(r'^image/detail$', search_views.by_image, name="by-image"),
    url(r'^image/detail/(?P<identifier>.*)$', search_views.detail, name="detail"),
]

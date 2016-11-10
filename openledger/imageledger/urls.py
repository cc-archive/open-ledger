from django.conf.urls import url, include

from imageledger.views import search_views
 
urlpatterns = [
    url(r'^$', search_views.index, name='index')

]

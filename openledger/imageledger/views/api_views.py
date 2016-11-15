import logging

from django.http import Http404, JsonResponse, HttpResponse, QueryDict
from django.views import View
from rest_framework import mixins, generics, serializers

from imageledger import models, api

log = logging.getLogger(__name__)

class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.List
        fields = ('title', 'slug', 'created_on', 'updated_on', 'creator_displayname')

class ListList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):
    queryset = models.List.objects.all()
    serializer_class = ListSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

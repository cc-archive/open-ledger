import logging

from django.http import Http404, JsonResponse, HttpResponse, QueryDict
from django.views import View
from django.shortcuts import get_object_or_404
from rest_framework import mixins, generics, serializers, status
from rest_framework.response import Response

from imageledger import models, api

log = logging.getLogger(__name__)


class ImageSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    title = serializers.CharField()
    url = serializers.URLField()
    creator = serializers.CharField()

class ListImageSerializer(serializers.Serializer):
    images = ImageSerializer(many=True)
    title = serializers.CharField()
    description = serializers.CharField()
    slug = serializers.CharField()
    created_on = serializers.DateTimeField()
    updated_on = serializers.DateTimeField()
    creator_displayname = serializers.CharField()

    def validate(self, data):
        data['image_objs'] = []
        for img in data['images']:
            data['image_objs'].append(models.Image.objects.get(identifier=img['identifier']))
        return data

    def update(self, instance, validated_data):
        instance.images.clear()
        for img in validated_data['image_objs']:
            instance.images.add(img)
        return instance


class ListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.List
        fields = ('title', 'slug', 'created_on', 'updated_on', 'description', 'creator_displayname')

class ListList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):
    queryset = models.List.objects.all()
    serializer_class = ListImageSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = ListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = models.List.objects.all()
    serializer_class = ListImageSerializer
    lookup_field = 'slug'

    def get(self, request, slug, **kwargs):
        return get_object_or_404(models.List, slug=slug)


    def put(self, request, slug, **kwargs):
        lst = models.List.objects.get(slug=slug)
        serializer = ListImageSerializer(lst, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

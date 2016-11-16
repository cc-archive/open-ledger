import logging

from django.http import Http404, JsonResponse, HttpResponse, QueryDict
from django.views import View
from django.shortcuts import get_object_or_404
from rest_framework import mixins, generics, serializers, status
from rest_framework.response import Response
from rest_framework import permissions

from imageledger import models

log = logging.getLogger(__name__)


class ListPermissions(permissions.BasePermission):
    """
     - owner may PUT, POST, DELETE
     - everyone can GET if the list is_public
    """

    def has_permission(self, request, view):
        # POST requests require auth at this time
        if request.method == 'POST' and not request.user.is_authenticated():
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # Allow GET requests for all
        if request.method == 'GET' and obj.is_public:
            return True
        else:
            return request.user == obj.owner

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
        if 'images' in data:
            for img in data['images']:
                try:
                    img = models.Image.objects.get(identifier=img['identifier'])
                    data['image_objs'].append(img)
                except models.Image.DoesNotExist:
                    raise Http404

        return data


    def update(self, instance, validated_data, **kwargs):
        if validated_data['replace_images']:
            instance.images.clear()
        for img in validated_data['image_objs']:
            if img.lists.filter(id=instance.id).count() == 0:
                instance.images.add(img)
        return instance


class ListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.List
        fields = ('title', 'slug', 'created_on', 'updated_on', 'description',
                  'creator_displayname', 'owner')

# Views

class ListList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    serializer_class = ListSerializer
    permission_classes = (ListPermissions, )

    def get_queryset(self):
        queryset = models.List.objects.all()
        title = self.request.query_params.get('title', None)
        if title is not None:
            queryset = queryset.filter(title__startswith=title)
        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = ListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = models.List.objects.all()
    serializer_class = ListImageSerializer
    lookup_field = 'slug'
    permission_classes = (ListPermissions, )

    def get_object(self):
        filters = {}
        filters[self.lookup_field] = self.kwargs[self.lookup_field]
        lst = get_object_or_404(self.get_queryset(), **filters)
        self.check_object_permissions(self.request, lst)
        return lst

    def get(self, request, slug, **kwargs):
        lst = self.get_object()

        serializer = ListImageSerializer(lst, data=request.data, partial=True)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, slug=None, **kwargs):
        lst = self.get_object()

        replace_images = True if 'replace' in request.data else False

        serializer = ListImageSerializer(lst, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(replace_images=replace_images)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug, **kwargs):
        """Passing an `images` param will delete the images; passing none will delete the instance"""
        lst = self.get_object()

        serializer = ListImageSerializer(lst, data=request.data, partial=True)
        delete_images_only = 'images' in request.data and len(request.data['images']) > 0

        if serializer.is_valid():
            if delete_images_only:
                for img in serializer.validated_data['image_objs']:
                    lst.images.remove(img)
            else:
                lst.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

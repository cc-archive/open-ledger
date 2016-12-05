import logging

from django.http import Http404, JsonResponse, HttpResponse, QueryDict
from django.views import View
from django.shortcuts import get_object_or_404
from rest_framework import mixins, generics, serializers, status
from rest_framework.response import Response
from rest_framework import permissions

from imageledger import models

log = logging.getLogger(__name__)

class AutocompletePermissions(permissions.BasePermission):
    """Only a logged-in user can use this endpoint, and only an object owner can GET matches."""

    def has_permission(self, request, view):
        # POST requests require auth at this time
        if request.method == 'GET' and request.user.is_authenticated():
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # Allow GET requests for owner
        if request.method == 'GET' and request.user == obj.owner:
            return True
        return False

class TagAutocompletePermissions(AutocompletePermissions):
    pass

class ListAutocompletePermissions(AutocompletePermissions):
    pass

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

class FavoritePermissions(permissions.IsAuthenticated):
    """You can only see your own favorites"""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user

class ImageSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    title = serializers.CharField()
    url = serializers.URLField()
    creator = serializers.CharField()

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ('name', 'created_on', 'updated_on', 'source')

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

class FavoriteReadSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    class Meta:
        model = models.Favorite
        fields = ('image', 'user', 'created_on', 'updated_on')

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Favorite
        fields = ('image', 'user', 'created_on', 'updated_on')

class UserTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserTags
        fields = ('image', 'user', 'tag', 'created_on', 'updated_on')

class UserTagReadSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    tag = TagSerializer()
    class Meta:
        model = models.UserTags
        fields = ('image', 'user', 'tag', 'created_on', 'updated_on')

# Views

class ListList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    queryset = models.List.objects.all()
    serializer_class = ListSerializer
    permission_classes = (ListPermissions, )


    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = ListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListAutocomplete(mixins.ListModelMixin,
                       generics.GenericAPIView):
    """A view for the List autocomplete feature, which will match, by title, only
    Lists which are owned by the requestor."""
    serializer_class = ListSerializer
    permission_classes = (ListAutocompletePermissions, )
    queryset = models.List.objects.all()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        queryset = queryset.filter(owner=self.request.user)
        title = self.request.query_params.get('title', None)
        if title is not None:
            queryset = queryset.filter(title__startswith=title)
        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

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

class FavoriteList(mixins.ListModelMixin,
                  generics.GenericAPIView):

    serializer_class = FavoriteReadSerializer
    permission_classes = (FavoritePermissions,)

    def get_queryset(self):
        return models.Favorite.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class FavoriteDetail(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.CreateModelMixin,
                     generics.GenericAPIView):
    queryset = models.Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (FavoritePermissions,)

    def get(self, request, *args, **kwargs):
        """Check if an image/user pair has a favorite or not."""
        fave = models.Favorite.objects.filter(image__identifier=self.kwargs.get('identifier'),
                                              user=request.user)
        if fave.count() == 1:
            serializer = FavoriteReadSerializer(fave.first())
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)


    def post(self, request, *args, **kwargs):
        img = models.Image.objects.get(identifier=self.kwargs.get('identifier'))
        serializer = FavoriteSerializer(data={'image': img.pk, 'user': request.user.pk})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        img = models.Image.objects.get(identifier=self.kwargs.get('identifier'))
        instance, created = models.Favorite.objects.get_or_create(image=img, user=request.user)
        serializer = FavoriteSerializer(instance, data={'image': img.pk, 'user': request.user.pk})
        if serializer.is_valid():
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(serializer.data, status=status_code)
        log.warn(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        fave = get_object_or_404(models.Favorite, image__identifier=self.kwargs.get('identifier'))
        fave.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserTagDetail(mixins.DestroyModelMixin,
                    mixins.CreateModelMixin,
                    generics.GenericAPIView):

    queryset = models.UserTags.objects.all()
    serializer_class = UserTagSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        img = models.Image.objects.get(identifier=request.data.get('identifier'))
        tag, created = models.Tag.objects.get_or_create(name=request.data.get('tag'))
        # If this tag didn't exist, create is as a user tag
        if created:
            tag.source = 'user'
            tag.save()
        serializer = UserTagSerializer(data={'image': img.pk, 'user': request.user.pk, 'tag': tag.pk})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user_tag = get_object_or_404(models.UserTags,
                                     user=request.user,
                                     image__identifier=self.kwargs.get('identifier'),
                                     tag__name=self.kwargs.get('tag'))

        user_tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserTagsList(mixins.ListModelMixin,
                   generics.GenericAPIView):

    serializer_class = UserTagReadSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return models.UserTags.objects.filter(user=self.request.user,
                                              image__identifier=self.kwargs.get('identifier'))

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class UserTagsAutocomplete(mixins.ListModelMixin,
                           generics.GenericAPIView):
    """A view for the Tags autocomplete feature, which will match, by title, only
    Tags which were created by the requestor."""
    serializer_class = UserTagReadSerializer
    permission_classes = (TagAutocompletePermissions, )
    queryset = models.UserTags.objects.all()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        queryset = queryset.filter(user=self.request.user)
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(tag__name__startswith=name)
        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

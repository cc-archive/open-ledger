from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404

from imageledger import models

class OwnedTagsMixin(object):

    def get_queryset(self):
        """Tags owned by the current user only"""
        qs = super().get_queryset()
        # Get the distinct set of tags
        qs = qs.filter(user_tags__user=self.request.user).distinct()
        return qs

class UserTagsList(LoginRequiredMixin, OwnedTagsMixin, ListView):
    model = models.Tag
    template_name = "user-tags-list.html"
    raise_exception = False


class UserTagsDetail(LoginRequiredMixin, ListView):
    template_name = "user-tags.html"
    model = models.Tag

    def get_queryset(self):
        """Images owned by the current user only; 302 if anon"""
        # Get the distinct set of images
        qs = models.Image.objects.filter(user_tags__user=self.request.user,
                       user_tags__tag__slug=self.kwargs.get('slug')).distinct()
        return qs

    def render_to_response(self, context):
        tag = get_object_or_404(models.Tag, slug=self.kwargs.get('slug'))
        context['tag'] = tag
        return super().render_to_response(context)

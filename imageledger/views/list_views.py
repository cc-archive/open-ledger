from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, Http404

from imageledger import models

class OwnedListMixin(object):

    def get_queryset(self):
        """Lists owned by the current user only"""
        qs = super().get_queryset()
        qs = qs.filter(owner=self.request.user)
        return qs

class OLListDetail(DetailView):
    model = models.List
    template_name = "list-public.html"
    fields = ['title', 'description', 'creator_displayname', 'images']

    def render_to_response(self, context):
        if not self.request.user.is_anonymous() and self.object.owner == self.request.user:
            return HttpResponseRedirect(reverse_lazy('my-list-update', kwargs={'slug': self.object.slug}))
        return super().render_to_response(context)

    def get_queryset(self):
        """Public lists only, or the user's own list"""
        qs = super().get_queryset()

        if self.request.user.is_anonymous():
            qs = qs.filter(is_public=True)
        else:
            qs = qs.filter(Q(owner=self.request.user) | Q(is_public=True))
        return qs


class OLListCreate(LoginRequiredMixin, CreateView):
    model = models.List
    template_name = "list.html"
    fields = ['title', 'description', 'is_public', 'creator_displayname']

class OLListUpdate(LoginRequiredMixin, OwnedListMixin, UpdateView):
    model = models.List
    template_name = "list.html"
    fields = ['title', 'description', 'is_public', 'creator_displayname']

    def get_object(self):
        try:
            obj = super().get_object()
            return obj
        except Http404:
            return None  # Don't raise 404 here, do that in render_to_response so we can redirect

    def render_to_response(self, context):
        if not context.get('object'):
            return HttpResponseRedirect(reverse_lazy('list-detail', kwargs=self.kwargs))
        return super().render_to_response(context)

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('list-detail', kwargs=self.kwargs))

class OLListDelete(LoginRequiredMixin, OwnedListMixin, DeleteView):
    model = models.List
    success_url = reverse_lazy('my-lists')

class OLOwnedListList(LoginRequiredMixin, OwnedListMixin, ListView):
    model = models.List
    template_name = "lists.html"
    raise_exception = False

    def get_context_data(self, **kwargs):
        """Get the "list" of favorites as well"""
        context = super().get_context_data(**kwargs)
        context['favorites'] = models.Favorite.objects.filter(user=self.request.user)
        return context

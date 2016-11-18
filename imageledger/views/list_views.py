from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.urls import reverse_lazy

from imageledger import models

class AbstractListView(object):

    def get_queryset(self):
        """Lists owned by the current user only"""
        qs = super().get_queryset()
        qs = qs.filter(owner=self.request.user)
        return qs


class OLListCreate(LoginRequiredMixin, CreateView):
    model = models.List
    template_name = "list.html"
    fields = ['title', 'description', 'is_public', 'creator_displayname']

class OLListUpdate(LoginRequiredMixin, UpdateView, AbstractListView):
    model = models.List
    template_name = "list.html"
    fields = ['title', 'description', 'is_public', 'creator_displayname']

class OLListDelete(LoginRequiredMixin, DeleteView, AbstractListView):
    model = models.List
    success_url = reverse_lazy('my-lists')

class OLOwnedListList(LoginRequiredMixin, ListView, AbstractListView):
    model = models.List
    template_name = "lists.html"

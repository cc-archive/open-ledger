from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.urls import reverse_lazy

from imageledger import models

class OLListCreate(CreateView):
    model = models.List
    template_name = "list.html"
    fields = ['title', 'description', 'is_public', 'creator_displayname']

class OLListUpdate(UpdateView):
    model = models.List
    template_name = "list.html"
    fields = ['title', 'description', 'is_public', 'creator_displayname']

class OLListDelete(DeleteView):
    model = models.List
    success_url = reverse_lazy('list-list')

class OLOwnedListList(ListView):
    model = models.List
    template_name = "lists.html"

    def get_queryset(self):
        """Lists owned by the current user only"""
        qs = super().get_queryset()
        qs = qs.filter(owner=self.request.user)
        return qs

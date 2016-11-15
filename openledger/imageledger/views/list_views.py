from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from imageledger import models

class ListCreate(CreateView):
    model = models.List
    template_name = "list.html"
    fields = ['title', 'description', 'is_public', 'creator_displayname']

class ListUpdate(UpdateView):
    model = models.List
    template_name = "list.html"
    fields = ['title', 'description', 'is_public', 'creator_displayname']

class ListDelete(DeleteView):
    model = models.List
    success_url = reverse_lazy('list-list')

from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, Http404

from imageledger import models

class FavoriteList(LoginRequiredMixin, ListView):
    model = models.Favorite
    template_name = "favorites.html"
    raise_exception = False

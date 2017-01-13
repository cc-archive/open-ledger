from django import forms
from django.conf import settings

from imageledger import licenses, models

PROVIDER_PER_PAGE = 20

LICENSE_CHOICES = (
    ('ALL-$', 'Use for commercial purposes'),
    ('ALL-MOD', 'Modify, adapt, or build upon')
)
# Search within only these fields
FIELD_CHOICES = (
    ('title', 'Title'),
    ('creator', 'Creator'),
    ('tags', 'Tags')
)
FIELD_DEFAULT = ['title', 'tags',]

# Types of works
WORK_TYPES = (
    ('photos', 'Photographs'),
    ('cultural', 'Cultural works'),
)
WORK_TYPES_DEFAULT = [wt[0] for wt in WORK_TYPES]

# Providers (e.g. 'flickr')
PROVIDER_CHOICES = sorted([(p, settings.PROVIDERS[p]['display_name'],) for p in settings.PROVIDERS])
PROVIDER_DEFAULT = []

class SearchForm(forms.Form):
    initial_data = {'page': 1,
                    'per_page': settings.RESULTS_PER_PAGE,
                    'search_fields': FIELD_DEFAULT,
                    'work_types': WORK_TYPES_DEFAULT,
                    'licenses': [licenses.DEFAULT_LICENSE],
                    'providers': PROVIDER_DEFAULT}

    search = forms.CharField(label='Search', max_length=1000, required=False)
    licenses = forms.MultipleChoiceField(label='License', choices=LICENSE_CHOICES, required=False,
                                         widget=forms.CheckboxSelectMultiple)

    # This is the only required field, as otherwise we have no idea what to search for
    search_fields = forms.MultipleChoiceField(label='Fields', choices=FIELD_CHOICES,
                                              widget=forms.CheckboxSelectMultiple)
    work_types = forms.MultipleChoiceField(label='Work type', choices=WORK_TYPES, required=False,
                                           widget=forms.CheckboxSelectMultiple)
    page = forms.IntegerField(widget=forms.HiddenInput, required=False)
    providers = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                          required=False,
                                          choices=PROVIDER_CHOICES)
    per_page = forms.IntegerField(widget=forms.HiddenInput, required=False)

class ListForm(forms.ModelForm):
    class Meta:
        model = models.List
        fields = ['title', 'is_public', 'description', 'images', 'creator_displayname']

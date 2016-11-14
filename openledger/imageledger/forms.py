from django import forms

from imageledger import licenses

PER_PAGE = 20

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

# Types of work
WORK_TYPES = (
    ('photos', 'Photographs'),
    ('cultural', 'Cultural works'),
)
WORK_TYPE_DEFAULT = [wt[0] for wt in WORK_TYPES]
FIELD_DEFAULT = [field[0] for field in FIELD_CHOICES]

PROVIDER_CHOICES = (
    ('fpx', '500px'),
    ('flickr', 'Flickr'),
    ('rijks', 'Rijksmuseum'),
    ('wikimedia', 'Wikimedia Commons'),
)

PROVIDERS_ALL = [p[0] for p in PROVIDER_CHOICES if p[0]]

class SearchForm(forms.Form):
    initial_data = {'page': 1,
                     'per_page': PER_PAGE,
                     'search_fields': ['title', 'tags', 'creator'],
                     'work_types': ['photos', 'cultural'],
                     'licenses': [licenses.DEFAULT_LICENSE],
                     'providers': PROVIDERS_ALL}

    search = forms.CharField(label='Search', max_length=1000)
    licenses = forms.MultipleChoiceField(label='License', choices=LICENSE_CHOICES, required=False,
                                         widget=forms.CheckboxSelectMultiple)
    search_fields = forms.MultipleChoiceField(label='Fields', choices=FIELD_CHOICES, required=False,
                                              widget=forms.CheckboxSelectMultiple)
    work_types = forms.MultipleChoiceField(label='Work type', choices=WORK_TYPES, required=False,
                                           widget=forms.CheckboxSelectMultiple)
    page = forms.IntegerField(widget=forms.HiddenInput, required=False)
    providers = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, required=False, choices=PROVIDER_CHOICES)
    per_page = forms.IntegerField(widget=forms.HiddenInput, required=False)

class ListForm(forms.Form):
    title = forms.CharField(label='Title')
    description = forms.CharField(label='Description', widget=forms.Textarea)
    is_public = forms.BooleanField(label='Is public?', required=False, widget=forms.CheckboxInput)

from django import forms

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


class SearchForm(forms.Form):
    search = forms.CharField(label='Search', max_length=1000)
    licenses = forms.MultipleChoiceField(label='License', choices=LICENSE_CHOICES)
    search_fields = forms.MultipleChoiceField(label='Fields', choices=FIELD_CHOICES)
    work_types = forms.MultipleChoiceField(label='Work type', choices=WORK_TYPES)

class ListForm(forms.Form):
    title = forms.CharField(label='Title')
    description = forms.CharField(label='Description', widget=forms.Textarea)
    is_public = forms.BooleanField(label='Is public?', required=False)

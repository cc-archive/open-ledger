from django import forms
from django.conf import settings

from imageledger import licenses, models
from akismet import Akismet
from wordfilter import Wordfilter

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
FIELD_DEFAULT = ['title', 'tags', 'creator']

# Types of works
WORK_TYPES = (
    ('photos', 'Photographs'),
    ('cultural', 'Cultural works'),
)
WORK_TYPES_DEFAULT = [wt[0] for wt in WORK_TYPES]

# Providers (e.g. 'flickr')
PROVIDER_CHOICES = [(p, settings.PROVIDERS[p]['display_name'],) for p in settings.PROVIDERS]
PROVIDER_DEFAULT = [p for p in settings.PROVIDERS]

# Results per page choices
RESULTS_PER_PAGE_CHOICES = (
    ('20', '20'),
    ('50', '50'),
    ('100', '100'),
)
RESULTS_PER_PAGE_DEFAULT = '20'

class SearchForm(forms.Form):
    initial_data = {'page': 1,
                    'per_page': RESULTS_PER_PAGE_DEFAULT,
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
    per_page = forms.ChoiceField(label="Results per page",
                                 widget=forms.RadioSelect,
                                 required=False,
                                 choices=RESULTS_PER_PAGE_CHOICES)

class ListForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # important to "pop" added kwarg before call to parent's constructor
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    class Meta:
        model = models.List
        fields = ['title', 'is_public', 'description', 'creator_displayname']

    def clean_description(self):
        desc = self.cleaned_data['description']
        if settings.TESTING:
            check_spam = False
        else:
            akismet = Akismet(settings.AKISMET_KEY, blog="CC Search")
            check_spam = akismet.check(self.request.get_host(),
                                  user_agent=self.request.META.get('user-agent'),
                                  comment_author=self.request.user.username,
                                  comment_content=desc)
        wordfilter = Wordfilter()
        check_words = wordfilter.blacklisted(desc)
        if check_spam or check_words:
            raise forms.ValidationError("This description failed our spam or profanity check; the description has not been updated.")

        return desc

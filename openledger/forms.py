from flask_wtf import Form
from wtforms import StringField, SelectMultipleField, TextAreaField, BooleanField, validators
from wtforms import widgets

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
    ('cultural works', 'Cultural works'),
)
WORK_TYPE_DEFAULT = [wt[0] for wt in WORK_TYPES]
FIELD_DEFAULT = [field[0] for field in FIELD_CHOICES]

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class SearchForm(Form):
    search = StringField('Search', validators=[validators.DataRequired()])
    licenses = MultiCheckboxField('License', choices=LICENSE_CHOICES)
    search_fields = MultiCheckboxField('Fields', choices=FIELD_CHOICES)
    work_types = MultiCheckboxField('Work type', choices=WORK_TYPES)

class ListForm(Form):
    title = StringField('Title', validators=[validators.DataRequired()])
    description = TextAreaField('Description', [validators.optional(), validators.length(max=2000)])
    is_public = BooleanField('Is public?', [validators.optional()])

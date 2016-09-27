from flask_wtf import Form
from wtforms import StringField, SelectMultipleField
from wtforms.validators import DataRequired
from wtforms import widgets

LICENSES = (
    ("BY", "BY"),
    ("BY-NC", "BY-NC"),
    ("BY-ND", "BY-ND"),
    ("BY-SA", "BY-SA"),
    ("BY-NC-ND", "BY-NC-ND"),
    ("BY-NC-SA", "BY-NC-SA"),
    ("PDM", "PDM"),
    ("CC0", "CC0"),)

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class SearchForm(Form):
    search = StringField('Search', validators=[DataRequired()])
    licenses = MultiCheckboxField('License', choices=LICENSES)

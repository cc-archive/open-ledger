from flask_wtf import Form
from wtforms import StringField, SelectMultipleField
from wtforms.validators import DataRequired
from wtforms import widgets

from openledger.licenses import LICENSES

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

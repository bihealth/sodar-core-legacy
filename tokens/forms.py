from django import forms

# Projectroles dependency
from projectroles.forms import SODARForm


class UserTokenCreateForm(SODARForm):
    """This form allows token creation"""

    #: Time to live in hours
    ttl = forms.IntegerField(
        label='Time to live',
        min_value=0,
        required=True,
        initial=0,
        help_text='Time to live in hours, set to 0 for tokens that never '
        'expire.',
    )

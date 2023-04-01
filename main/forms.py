from django import forms
from . import models as m
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _


# extend UserCreationForm and add the email field bc it is not a default
# then specify the model to use and all the fields to be rendered
# the magic of using this UserCreationForm is that it takes care of hashing passwords, checking exceptions, and
# as soon as you get the form into the view and authenticate it, a new user will be automatically created
# by the form, and you can save it straight into the db without messing around User.objects.create or
# models or anything like that
class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='Email', max_length=100, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']


class ShippingForm(forms.ModelForm):
    class Meta:
        model = m.ShippingAddress
        fields = ['street_1', 'street_2', 'zip']
        labels = {
            'street_1': _('Street 1'),
            'street_2': _('Street 2'),
            'zip': _('Zip')
        }


# ------- FORMS FOR GUEST USERS ---------#

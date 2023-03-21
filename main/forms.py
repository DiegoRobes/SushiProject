from django import forms
from . import models as m
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class UserForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=100)
    last_name = forms.CharField(label='Last Name', max_length=100)
    email = forms.EmailField(label='Email', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput())
    password_confirm = forms.CharField(label='Password Confirm', widget=forms.PasswordInput())


class ShippingForm(forms.ModelForm):
    class Meta:
        model = m.ShippingAddress
        fields = {'street_1', 'street_2', 'zip'}
        labels = {
            'street_1': _('Street 1'),
            'street_2': _('Street 2'),
            'zip': _('Zip')
        }

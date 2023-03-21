from django import forms
from . import models as m
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class UserForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=100)
    last_name = forms.CharField(label='Last Name', max_length=100)
    email = forms.EmailField(label='Email', max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)


class ShippingForm(forms.ModelForm):
    class Meta:
        model = m.ShippingAddress
        fields = '__all__'

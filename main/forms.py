from django import forms
from . models import Customer


class CustomerRegistration(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['f_name', 'l_name', 'email']
        labels = {'f_name': 'First Name', 'l_name': 'Last Name', 'email': 'Email'}


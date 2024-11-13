from django.forms import ModelForm
from django import forms
from .models import ShippingInfo

class ShippingForm(ModelForm):
    class Meta:
        model = ShippingInfo
        exclude = ['user']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone (optional)'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'address_line_one': forms.TextInput(attrs={'placeholder': 'Street Address'}),
            'address_line_two': forms.TextInput(attrs={'placeholder': 'Floor / Appartement / Other (optional)'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'Zip Code'}),
        }

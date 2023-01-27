from django import forms
from django.forms import CharField, Textarea

from .models import Fund, Position, Security


# creating a form
class FundForm(forms.ModelForm):

    class Meta:
        # specify model to be used
        model = Fund

        # specify fields to be used
        fields = "__all__"


# creating a form
class PositionForm(forms.ModelForm):

    class Meta:
        # specify model to be used
        model = Position

        # specify fields to be used
        #fields = "__all__"
        fields = ['quantity', 'security', 'fund']

        #field_classes = {'security': forms.CharField}
        widgets = {'security': forms.TextInput}

# creating a form
class SecurityForm(forms.ModelForm):

    class Meta:
        # specify model to be used
        model = Security

        # specify fields to be used
        fields = "__all__"
        #readonly_fields = ['last_price',]

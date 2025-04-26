# forms.py
from django import forms
from .models import DragQueen
class ProfileForm(forms.ModelForm):
    """Form for creating and editing a drag queen profile"""
    class Meta:
        model = DragQueen
        exclude = ['user', 'created_at', 'updated_at']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 5}),
            'performance_style': forms.TextInput(attrs={'placeholder': 'Comedy, Pageant, Club Kid, etc.'}),
        }

"""
class ProfileMediaForm(forms.ModelForm):
    #Form for adding and editing profile media
    class Meta:
        model = ProfileMedia
        fields = ['media_type', 'file', 'caption', 'is_featured']

class ProductForm(forms.ModelForm):
    #Form for adding and editing merchandise products
    class Meta:
        model = Product
        exclude = ['profile', 'created_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

class GroupForm(forms.ModelForm):
    #Form for creating and editing drag groups
    class Meta:
        model = DragGroup
        fields = ['name', 'description', 'logo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class GroupEventForm(forms.ModelForm):
    #Form for creating and editing group events
    class Meta:
        model = GroupEvent
        exclude = ['group', 'created_at']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

"""
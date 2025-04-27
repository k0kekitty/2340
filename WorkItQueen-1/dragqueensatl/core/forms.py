# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    DragQueen, Performance, Review, ProfileMedia, 
    DragGroup, GroupEvent, GroupPhoto, EventPhoto
)

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    """Form for creating and editing a drag queen profile"""
    class Meta:
        model = DragQueen
        fields = ['name', 'bio', 'performance_style', 'location', 
                 'instagram', 'twitter', 'youtube', 'facebook', 'tiktok', 'merchandise']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your stage name'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'performance_style': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comedy, Pageant, Club Kid, etc.'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Atlanta, GA'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/yourusername'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/yourusername'}),
            'youtube': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/yourchannel'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/yourpage'}),
            'tiktok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://tiktok.com/@yourusername'}),
            'merchandise': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://etsy.com/shop/yourshop'}),
        }

class ProfileMediaForm(forms.ModelForm):
    """Form for adding and editing profile media"""
    class Meta:
        model = ProfileMedia
        fields = ['media_type', 'file', 'youtube_url', 'caption', 'is_featured']
        widgets = {
            'media_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/watch?v=...'}),
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short description of this media'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PerformanceForm(forms.ModelForm):
    """Form for adding and editing performances"""
    class Meta:
        model = Performance
        fields = ['title', 'venue', 'address', 'latitude', 'longitude', 'date', 
                 'time', 'description', 'price', 'ticket_link']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'ticket_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://ticketsite.com/yourevent'}),
        }

class ReviewForm(forms.ModelForm):
    """Form for submitting reviews"""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}, choices=[(i, f"{i} Stars") for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share your experience...'}),
        }

class GroupForm(forms.ModelForm):
    """Form for creating and editing drag groups"""
    class Meta:
        model = DragGroup
        fields = ['name', 'description', 'logo', 'is_public', 'allow_member_posts', 'allow_member_events']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_member_posts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_member_events': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class GroupEventForm(forms.ModelForm):
    """Form for creating and editing group events"""
    class Meta:
        model = GroupEvent
        fields = ['title', 'description', 'date', 'time', 'venue', 'address', 
                 'latitude', 'longitude', 'image', 'ticket_url', 'is_private']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'ticket_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class GroupPhotoForm(forms.ModelForm):
    """Form for uploading group photos"""
    class Meta:
        model = GroupPhoto
        fields = ['file', 'caption']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EventPhotoForm(forms.ModelForm):
    """Form for uploading event photos"""
    class Meta:
        model = EventPhoto
        fields = ['file', 'caption']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SearchForm(forms.Form):
    """Form for searching performances"""
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search performances...',
        'class': 'form-control'
    }))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'form-control'
    }))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'form-control'
    }))
    venue = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Venue name',
        'class': 'form-control'
    }))
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'City, state',
        'class': 'form-control'
    }))
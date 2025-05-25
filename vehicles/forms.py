from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserProfile, Collection, Vehicle, Review



class VehicleForm(forms.ModelForm):
    collections = forms.ModelMultipleChoiceField(
        queryset=Collection.objects.all(), 
        widget=forms.SelectMultiple,
        required=False,
        label="Select Collections"
    )

    class Meta:
        model = Vehicle
        fields = ['name', 'description', 'image', 'available', 'collections']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(VehicleForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['collections'].queryset = Collection.objects.filter(is_private=False) | Collection.objects.filter(owner=user)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your review here...'})
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        
    def __init__(self, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = ''

class VehicleSearchForm(forms.Form):
    query = forms.CharField(label='Search', max_length=100, required=False)

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['name', 'description', 'is_private']
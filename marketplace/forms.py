from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import ActivityUpdate, Application, Comment, Job, Message, Profile, Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('This email is already registered.')
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'category', 'job_type', 'salary', 'location',
            'latitude', 'longitude', 'deadline', 'required_skills', 'photo',
            'video', 'audio', 'document', 'contact_information', 'tags',
        ]
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'cover_photo', 'bio', 'skills', 'location', 'latitude', 'longitude', 'resume']
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {'body': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a helpful comment...'})}


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['message']
        widgets = {'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Introduce yourself and why you fit this job.'})}


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body', 'image', 'voice_note', 'attachment']
        widgets = {'body': forms.TextInput(attrs={'placeholder': 'Message...'})}


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'body', 'positive']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'body': forms.Textarea(attrs={'rows': 4}),
        }


class ActivityUpdateForm(forms.ModelForm):
    class Meta:
        model = ActivityUpdate
        fields = ['body', 'media']
        widgets = {'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share an update with your network...'})}

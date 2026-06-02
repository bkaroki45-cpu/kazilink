from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import ActivityUpdate, Application, AttachmentPost, Comment, Job, JobAlert, JobReview, Message, Profile, Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email address'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm password'})

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('This email is already registered.')
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class PasswordResetEmailForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Registered email address'}))

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if not User.objects.filter(email__iexact=email).exists():
            raise ValidationError('No account uses this email address.')
        return email


class PasswordResetOTPForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={'placeholder': '6-digit OTP', 'inputmode': 'numeric'}),
    )


class PasswordResetNewPasswordForm(SetPasswordForm):
    pass


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
            'location': forms.TextInput(attrs={
                'autocomplete': 'off',
                'data-location-search': '1',
                'placeholder': 'Search institution, road, hospital, ward, town...',
            }),
        }


class AttachmentPostForm(forms.ModelForm):
    class Meta:
        model = AttachmentPost
        fields = [
            'title', 'description', 'opportunity_type', 'organization', 'location',
            'deadline', 'required_skills', 'photo', 'document', 'contact_information',
        ]
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'location': forms.TextInput(attrs={'placeholder': 'Town, campus, company, or county'}),
        }


class JobReviewForm(forms.ModelForm):
    class Meta:
        model = JobReview
        fields = ['rating', 'body', 'positive']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'body': forms.Textarea(attrs={'rows': 4}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'cover_photo', 'bio', 'skills', 'location', 'latitude', 'longitude', 'resume']
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }


class JobAlertForm(forms.ModelForm):
    class Meta:
        model = JobAlert
        fields = [
            'keyword', 'category', 'job_type', 'location', 'latitude', 'longitude',
            'radius_km', 'salary_min', 'salary_max',
        ]
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'location': forms.TextInput(attrs={
                'autocomplete': 'off',
                'data-location-search': '1',
                'placeholder': 'Institution, landmark, road, ward, town...',
            }),
            'radius_km': forms.Select(choices=((5, '5 km'), (10, '10 km'), (20, '20 km'), (50, '50 km'))),
            'keyword': forms.TextInput(attrs={'placeholder': 'Title, skill, keyword'}),
            'salary_min': forms.NumberInput(attrs={'placeholder': 'Minimum'}),
            'salary_max': forms.NumberInput(attrs={'placeholder': 'Maximum'}),
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

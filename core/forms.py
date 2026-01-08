from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class StudyHubLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'username'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': '••••••••'}),
    )


class StudyHubRegisterForm(UserCreationForm):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'username'}),
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Придумайте пароль'}),
    )
    password2 = forms.CharField(
        label='Повтор пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Повторите пароль'}),
    )
    role = forms.ChoiceField(
        label='Роль',
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg'}),
        initial=UserProfile.ROLE_STUDENT,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)


class ProfileForm(forms.ModelForm):
    display_name = forms.CharField(
        label='Отображаемое имя',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Алия'}),
    )
    bio = forms.CharField(
        label='О себе',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Коротко о себе…'}),
    )

    class Meta:
        model = UserProfile
        fields = ('display_name', 'bio')



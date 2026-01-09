from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Note, Subject, Topic, UserProfile


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


class NoteForm(forms.ModelForm):
    title = forms.CharField(
        label='Заголовок',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок конспекта'}),
    )
    content = forms.CharField(
        label='Содержимое',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 15, 'placeholder': 'Введите содержимое конспекта...'}),
    )
    subject = forms.ModelChoiceField(
        label='Предмет',
        queryset=Subject.objects.none(),  # Будет установлен в __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='Выберите предмет (необязательно)',
    )
    topic = forms.ModelChoiceField(
        label='Тема',
        queryset=Topic.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='Выберите тему (необязательно)',
    )

    class Meta:
        model = Note
        fields = ('title', 'content', 'subject', 'topic')

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Всегда загружаем все предметы
        self.fields['subject'].queryset = Subject.objects.all().order_by('name')
        
        # Обрабатываем как POST данные, так и GET параметры
        subject_id = None
        if self.data:
            subject_id = self.data.get('subject')
        elif request and request.method == 'GET':
            subject_id = request.GET.get('subject')
        
        if subject_id:
            try:
                subject_id = int(subject_id)
                self.fields['topic'].queryset = Topic.objects.filter(subject_id=subject_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['topic'].queryset = Topic.objects.none()
        elif self.instance.pk:
            if self.instance.subject:
                self.fields['topic'].queryset = Topic.objects.filter(subject=self.instance.subject).order_by('name')
            else:
                self.fields['topic'].queryset = Topic.objects.none()
        else:
            self.fields['topic'].queryset = Topic.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        subject = cleaned_data.get('subject')
        topic = cleaned_data.get('topic')
        
        if not subject and not topic:
            raise ValidationError('Необходимо указать хотя бы предмет или тему.')
        
        if topic and subject and topic.subject != subject:
            raise ValidationError('Выбранная тема не относится к выбранному предмету.')
        
        return cleaned_data



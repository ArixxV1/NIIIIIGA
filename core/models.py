from django.conf import settings
from django.db import models


class Subject(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ['name']
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'

    def __str__(self) -> str:
        return self.name


class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['subject__name', 'name']
        verbose_name = 'Тема'
        verbose_name_plural = 'Темы'

    def __str__(self) -> str:
        return f'{self.subject.name} — {self.name}'


class Test(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['topic'], name='unique_test_per_topic'),
        ]
        ordering = ['topic__subject__name', 'topic__name']
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self) -> str:
        return f'{self.topic.name}: {self.title}'


class Question(models.Model):
    ANSWER_A = 'A'
    ANSWER_B = 'B'
    ANSWER_C = 'C'
    ANSWER_D = 'D'

    ANSWER_CHOICES = [
        (ANSWER_A, 'A'),
        (ANSWER_B, 'B'),
        (ANSWER_C, 'C'),
        (ANSWER_D, 'D'),
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self) -> str:
        return f'[{self.test.title}] {self.text[:60]}'


class Material(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['topic__subject__name', 'topic__name', 'order', 'id']
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'

    def __str__(self) -> str:
        return f'{self.topic.name}: {self.title}'


class TestAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    correct_count = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    percent = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Попытка теста'
        verbose_name_plural = 'Попытки тестов'

    def __str__(self) -> str:
        return f'{self.user} — {self.test.title} — {self.percent:.0f}%'


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='attempt_answers')
    selected_answer = models.CharField(max_length=1, choices=Question.ANSWER_CHOICES, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = [('attempt', 'question')]
        verbose_name = 'Ответ в попытке'
        verbose_name_plural = 'Ответы в попытках'

    def __str__(self) -> str:
        return f'{self.attempt_id}: {self.question_id} — {self.selected_answer}'


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=80, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self) -> str:
        return self.display_name or str(self.user)

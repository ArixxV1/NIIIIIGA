from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Count, Exists, OuterRef, Max

from .forms import ProfileForm, StudyHubLoginForm, StudyHubRegisterForm
from .models import AttemptAnswer, Material, Subject, Test, TestAttempt, Topic, UserProfile


def home(request: HttpRequest) -> HttpResponse:
    subjects = Subject.objects.annotate(topic_count=Count('topics')).all()
    stats = {
        'subjects': Subject.objects.count(),
        'topics': Topic.objects.count(),
        'tests': Test.objects.count(),
    }
    return render(request, 'core/home.html', {'subjects': subjects, 'stats': stats})


def subject_detail(request: HttpRequest, id: int) -> HttpResponse:
    subject = get_object_or_404(Subject, pk=id)
    topics = (
        subject.topics.annotate(
            has_test=Exists(Test.objects.filter(topic=OuterRef('pk'))),
        )
        .all()
    )
    return render(
        request,
        'core/subject_detail.html',
        {
            'subject': subject,
            'topics': topics,
        },
    )


def topic_detail(request: HttpRequest, id: int) -> HttpResponse:
    topic = get_object_or_404(Topic, pk=id)
    test = topic.tests.first()
    materials = topic.materials.all().order_by('order', 'id')

    best_percent = None
    if request.user.is_authenticated and test:
        best_percent = (
            TestAttempt.objects.filter(user=request.user, test=test).aggregate(best=Max('percent')).get('best')
        )

    return render(
        request,
        'core/topic_detail.html',
        {
            'topic': topic,
            'test': test,
            'materials': materials,
            'best_percent': best_percent,
        },
    )


def materials_view(request: HttpRequest, id: int) -> HttpResponse:
    topic = get_object_or_404(Topic, pk=id)
    materials = topic.materials.all().order_by('order', 'id')
    test = topic.tests.first()
    return render(
        request,
        'core/materials.html',
        {
            'topic': topic,
            'materials': materials,
            'test': test,
        },
    )


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('profile')

    next_url = request.GET.get('next') or reverse('profile')
    form = StudyHubLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, 'Вы вошли в аккаунт.')
        return redirect(next_url)

    return render(request, 'core/auth/login.html', {'form': form, 'next': next_url})


def register_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('profile')

    form = StudyHubRegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        UserProfile.objects.get_or_create(user=user)
        login(request, user)
        messages.success(request, 'Аккаунт создан. Добро пожаловать в StudyHub!')
        return redirect('profile')

    return render(request, 'core/auth/register.html', {'form': form})


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('home')


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Профиль обновлён.')
        return redirect('profile')

    attempts = (
        TestAttempt.objects.select_related('test', 'test__topic', 'test__topic__subject')
        .filter(user=request.user)
        .all()[:20]
    )

    best_by_topic = (
        TestAttempt.objects.filter(user=request.user)
        .values('test__topic_id', 'test__topic__name', 'test__topic__subject__name')
        .annotate(best=Max('percent'), attempts=Count('id'))
        .order_by('test__topic__subject__name', 'test__topic__name')
    )

    return render(
        request,
        'core/profile.html',
        {
            'profile': profile,
            'form': form,
            'attempts': attempts,
            'best_by_topic': best_by_topic,
        },
    )


def test_take(request: HttpRequest, id: int) -> HttpResponse:
    test = get_object_or_404(
        Test.objects.select_related('topic', 'topic__subject').prefetch_related('questions'),
        pk=id,
    )
    questions = list(test.questions.all())

    if request.method == 'POST':
        results = []
        correct_count = 0

        for q in questions:
            selected = request.POST.get(f'q_{q.id}', '').strip()
            is_correct = bool(selected) and selected == q.correct_answer
            if is_correct:
                correct_count += 1

            option_map = {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d,
            }

            results.append(
                {
                    'question': q,
                    'selected': selected,
                    'is_correct': is_correct,
                    'correct': q.correct_answer,
                    'selected_text': option_map.get(selected, ''),
                    'correct_text': option_map.get(q.correct_answer, ''),
                }
            )

        total = len(questions)
        percent = (correct_count / total * 100) if total else 0

        saved_attempt = None
        if request.user.is_authenticated:
            saved_attempt = TestAttempt.objects.create(
                user=request.user,
                test=test,
                correct_count=correct_count,
                total=total,
                percent=percent,
            )
            for r in results:
                q = r['question']
                AttemptAnswer.objects.create(
                    attempt=saved_attempt,
                    question=q,
                    selected_answer=r['selected'],
                    is_correct=r['is_correct'],
                )

        return render(
            request,
            'core/test_result.html',
            {
                'test': test,
                'results': results,
                'correct_count': correct_count,
                'total': total,
                'percent': percent,
                'saved_attempt': saved_attempt,
            },
        )

    return render(request, 'core/test_take.html', {'test': test, 'questions': questions})

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Count, Exists, OuterRef, Max, Avg

from .forms import NoteForm, ProfileForm, StudyHubLoginForm, StudyHubRegisterForm
from .models import AttemptAnswer, Material, Note, Subject, Test, TestAttempt, Topic, UserProfile, TeacherStudent


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
        profile, created = UserProfile.objects.get_or_create(user=user)
        # Всегда устанавливаем роль из формы (на случай, если профиль уже создан сигналом)
        profile.role = form.cleaned_data.get('role', UserProfile.ROLE_STUDENT)
        profile.save()
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
    
    # Если роль не установлена, устанавливаем по умолчанию student
    if not profile.role:
        profile.role = UserProfile.ROLE_STUDENT
        profile.save()

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


@login_required
def teacher_dashboard(request: HttpRequest) -> HttpResponse:
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_teacher:
        messages.error(request, 'Доступно только для учителей.')
        return redirect('profile')
    
    students = TeacherStudent.objects.filter(teacher=profile).select_related('student', 'student__user')
    student_count = students.count()
    max_students = TeacherStudent.MAX_STUDENTS_PER_TEACHER
    
    # Получаем успеваемость для каждого ученика
    students_with_performance = []
    for ts in students:
        student = ts.student
        attempts = TestAttempt.objects.filter(user=student.user).select_related('test', 'test__topic', 'test__topic__subject')
        
        # Статистика по ученику
        total_attempts = attempts.count()
        avg_percent = attempts.aggregate(avg=Avg('percent'))['avg'] or 0
        best_attempt = attempts.order_by('-percent').first()
        
        # Группировка по темам
        topic_stats = (
            attempts.values('test__topic__name', 'test__topic__subject__name')
            .annotate(best=Max('percent'), count=Count('id'))
            .order_by('test__topic__subject__name', 'test__topic__name')[:10]
        )
        
        students_with_performance.append({
            'teacher_student': ts,
            'student': student,
            'total_attempts': total_attempts,
            'avg_percent': avg_percent,
            'best_attempt': best_attempt,
            'topic_stats': topic_stats,
        })
    
    return render(
        request,
        'core/teacher_dashboard.html',
        {
            'profile': profile,
            'students_with_performance': students_with_performance,
            'student_count': student_count,
            'max_students': max_students,
        },
    )


@login_required
def teacher_invite_student(request: HttpRequest) -> HttpResponse:
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_teacher:
        messages.error(request, 'Доступно только для учителей.')
        return redirect('profile')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        if not username:
            messages.error(request, 'Введите имя пользователя.')
            return redirect('teacher_invite')
        
        try:
            student_user = User.objects.get(username=username)
            student_profile = get_object_or_404(UserProfile, user=student_user)
            
            if not student_profile.is_student:
                messages.error(request, f'Пользователь {username} не является учеником.')
                return redirect('teacher_invite')
            
            # Проверка лимита
            current_count = TeacherStudent.objects.filter(teacher=profile).count()
            if current_count >= TeacherStudent.MAX_STUDENTS_PER_TEACHER:
                messages.error(request, f'Достигнут лимит учеников ({TeacherStudent.MAX_STUDENTS_PER_TEACHER}).')
                return redirect('teacher_dashboard')
            
            # Проверка существующей связи
            if TeacherStudent.objects.filter(teacher=profile, student=student_profile).exists():
                messages.warning(request, f'Ученик {username} уже добавлен.')
                return redirect('teacher_dashboard')
            
            # Создание связи
            TeacherStudent.objects.create(teacher=profile, student=student_profile)
            messages.success(request, f'Ученик {username} успешно добавлен.')
            return redirect('teacher_dashboard')
            
        except User.DoesNotExist:
            messages.error(request, f'Пользователь {username} не найден.')
            return redirect('teacher_invite')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('teacher_invite')
    
    return render(request, 'core/teacher_invite.html', {'profile': profile})


@login_required
def teacher_remove_student(request: HttpRequest, id: int) -> HttpResponse:
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_teacher:
        messages.error(request, 'Доступно только для учителей.')
        return redirect('profile')
    
    teacher_student = get_object_or_404(TeacherStudent, pk=id, teacher=profile)
    student_username = teacher_student.student.user.username
    teacher_student.delete()
    messages.success(request, f'Ученик {student_username} удалён из вашего списка.')
    return redirect('teacher_dashboard')


@login_required
def student_select_teacher(request: HttpRequest) -> HttpResponse:
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_student:
        messages.error(request, 'Доступно только для учеников.')
        return redirect('profile')
    
    # Получаем текущих учителей
    current_teachers = TeacherStudent.objects.filter(student=profile).select_related('teacher', 'teacher__user')
    current_teacher_ids = set(ts.teacher_id for ts in current_teachers)
    
    # Поиск учителей
    search_query = request.GET.get('search', '').strip()
    teachers = UserProfile.objects.filter(role=UserProfile.ROLE_TEACHER).select_related('user')
    
    if search_query:
        # Поиск по username или display_name
        teachers = teachers.filter(
            user__username__icontains=search_query
        ) | teachers.filter(
            display_name__icontains=search_query
        )
    
    # Исключаем уже выбранных учителей
    teachers = teachers.exclude(id__in=current_teacher_ids).order_by('user__username')
    
    # Добавляем количество учеников для каждого учителя
    teachers_with_count = []
    for teacher in teachers:
        student_count = TeacherStudent.objects.filter(teacher=teacher).count()
        teachers_with_count.append({
            'teacher': teacher,
            'student_count': student_count,
            'can_add': student_count < TeacherStudent.MAX_STUDENTS_PER_TEACHER,
        })
    
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        if teacher_id:
            try:
                teacher_profile = get_object_or_404(UserProfile, pk=teacher_id, role=UserProfile.ROLE_TEACHER)
                
                # Проверка лимита учителя
                current_count = TeacherStudent.objects.filter(teacher=teacher_profile).count()
                if current_count >= TeacherStudent.MAX_STUDENTS_PER_TEACHER:
                    messages.error(request, f'Учитель {teacher_profile.user.username} достиг лимита учеников.')
                    return redirect('student_select_teacher')
                
                # Проверка существующей связи
                if TeacherStudent.objects.filter(teacher=teacher_profile, student=profile).exists():
                    messages.warning(request, 'Вы уже выбрали этого учителя.')
                    return redirect('student_select_teacher')
                
                # Создание связи
                TeacherStudent.objects.create(teacher=teacher_profile, student=profile)
                messages.success(request, f'Учитель {teacher_profile.user.username} добавлен.')
                return redirect('student_select_teacher')
                
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('student_select_teacher')
    
    return render(
        request,
        'core/student_select_teacher.html',
        {
            'profile': profile,
            'current_teachers': current_teachers,
            'teachers_with_count': teachers_with_count,
            'search_query': search_query,
        },
    )


@login_required
def student_leave_teacher(request: HttpRequest, id: int) -> HttpResponse:
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_student:
        messages.error(request, 'Доступно только для учеников.')
        return redirect('profile')
    
    teacher_student = get_object_or_404(TeacherStudent, pk=id, student=profile)
    teacher_username = teacher_student.teacher.user.username
    teacher_student.delete()
    messages.success(request, f'Вы покинули учителя {teacher_username}.')
    return redirect('student_select_teacher')


def notes_list(request: HttpRequest) -> HttpResponse:
    notes = Note.objects.select_related('user', 'subject', 'topic').all()
    
    # Фильтрация
    subject_id = request.GET.get('subject')
    topic_id = request.GET.get('topic')
    author_id = request.GET.get('author')
    
    if subject_id:
        notes = notes.filter(subject_id=subject_id)
    if topic_id:
        notes = notes.filter(topic_id=topic_id)
    if author_id:
        notes = notes.filter(user_id=author_id)
    
    subjects = Subject.objects.all()
    topics = Topic.objects.all() if not subject_id else Topic.objects.filter(subject_id=subject_id)
    
    return render(
        request,
        'core/notes/note_list.html',
        {
            'notes': notes,
            'subjects': subjects,
            'topics': topics,
            'selected_subject': int(subject_id) if subject_id else None,
            'selected_topic': int(topic_id) if topic_id else None,
            'selected_author': int(author_id) if author_id else None,
        },
    )


@login_required
def note_create(request: HttpRequest) -> HttpResponse:
    form = NoteForm(request.POST or None, request=request)
    if request.method == 'POST':
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            messages.success(request, 'Конспект успешно создан.')
            return redirect('note_detail', id=note.id)
    
    return render(request, 'core/notes/note_create.html', {'form': form})


def note_detail(request: HttpRequest, id: int) -> HttpResponse:
    note = get_object_or_404(Note.objects.select_related('user', 'subject', 'topic'), pk=id)
    is_owner = request.user.is_authenticated and note.user == request.user
    
    return render(
        request,
        'core/notes/note_detail.html',
        {
            'note': note,
            'is_owner': is_owner,
        },
    )


@login_required
def note_edit(request: HttpRequest, id: int) -> HttpResponse:
    note = get_object_or_404(Note, pk=id, user=request.user)
    form = NoteForm(request.POST or None, instance=note, request=request)
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Конспект успешно обновлён.')
            return redirect('note_detail', id=note.id)
    
    return render(request, 'core/notes/note_edit.html', {'form': form, 'note': note})


@login_required
def note_delete(request: HttpRequest, id: int) -> HttpResponse:
    note = get_object_or_404(Note, pk=id, user=request.user)
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Конспект удалён.')
        return redirect('notes_list')
    
    return render(request, 'core/notes/note_delete.html', {'note': note})


@login_required
def my_notes(request: HttpRequest) -> HttpResponse:
    notes = Note.objects.filter(user=request.user).select_related('subject', 'topic').order_by('-created_at')
    
    return render(request, 'core/notes/my_notes.html', {'notes': notes})


def load_topics(request: HttpRequest) -> HttpResponse:
    """AJAX endpoint для загрузки тем по предмету"""
    from django.http import JsonResponse
    subject_id = request.GET.get('subject_id')
    if subject_id:
        try:
            topics = Topic.objects.filter(subject_id=subject_id).order_by('name')
            topics_data = [{'id': topic.id, 'name': topic.name} for topic in topics]
            return JsonResponse({'topics': topics_data})
        except (ValueError, TypeError):
            return JsonResponse({'topics': []})
    return JsonResponse({'topics': []})

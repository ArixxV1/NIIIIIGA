from django.contrib import admin

from .models import (
    AttemptAnswer,
    Material,
    Note,
    Question,
    Subject,
    TeacherStudent,
    Test,
    TestAttempt,
    Topic,
    UserProfile,
)


class TopicInline(admin.StackedInline):
    model = Topic
    extra = 0
    fields = ('name', 'description')
    show_change_link = True


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'topic_count')
    search_fields = ('name', 'description')
    fields = ('name', 'image', 'description')
    inlines = [TopicInline]
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if obj.description and len(obj.description) > 50 else obj.description or '-'
    description_short.short_description = 'Описание'
    
    def topic_count(self, obj):
        return obj.topics.count()
    topic_count.short_description = 'Тем'


class TestInline(admin.StackedInline):
    model = Test
    extra = 0
    max_num = 1
    fields = ('title',)
    show_change_link = True


class MaterialInline(admin.StackedInline):
    model = Material
    extra = 0
    fields = ('order', 'title', 'content')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    list_filter = ('subject',)
    search_fields = ('name', 'subject__name')
    inlines = [TestInline, MaterialInline]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'order')
    list_filter = ('topic__subject', 'topic')
    search_fields = ('title', 'topic__name', 'topic__subject__name')
    ordering = ('topic__subject__name', 'topic__name', 'order', 'id')


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    fields = (
        'text',
        'option_a',
        'option_b',
        'option_c',
        'option_d',
        'correct_answer',
        'explanation',
    )


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'subject_name')
    list_filter = ('topic__subject',)
    search_fields = ('title', 'topic__name', 'topic__subject__name')
    inlines = [QuestionInline]

    @admin.display(description='Предмет')
    def subject_name(self, obj: Test) -> str:
        return obj.topic.subject.name


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'test', 'correct_answer')
    list_filter = ('test__topic__subject', 'test')
    search_fields = ('text', 'test__title')

    @admin.display(description='Вопрос')
    def short_text(self, obj: Question) -> str:
        return obj.text[:80]


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    fields = ('question', 'selected_answer', 'is_correct')
    readonly_fields = ('question', 'selected_answer', 'is_correct')
    can_delete = False


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'percent', 'correct_count', 'total', 'created_at')
    list_filter = ('test__topic__subject', 'test')
    search_fields = ('user__username', 'test__title', 'test__topic__name', 'test__topic__subject__name')
    ordering = ('-created_at',)
    inlines = [AttemptAnswerInline]
    readonly_fields = ('user', 'test', 'correct_count', 'total', 'percent', 'created_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'role', 'has_avatar', 'has_links')
    list_filter = ('role',)
    search_fields = ('user__username', 'display_name', 'bio')
    fields = ('user', 'role', 'display_name', 'bio', 'avatar', 'website', 'github', 'telegram', 'vk')
    
    @admin.display(boolean=True, description='Есть фото')
    def has_avatar(self, obj):
        return bool(obj.avatar)
    
    @admin.display(boolean=True, description='Есть ссылки')
    def has_links(self, obj):
        return bool(obj.website or obj.github or obj.telegram or obj.vk)


@admin.register(TeacherStudent)
class TeacherStudentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'student', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('teacher__user__username', 'student__user__username', 'teacher__display_name', 'student__display_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'subject', 'topic', 'created_at')
    list_filter = ('subject', 'created_at')
    search_fields = ('title', 'content', 'user__username', 'subject__name', 'topic__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('subject/<int:id>', views.subject_detail, name='subject_detail'),
    path('subject/<int:id>/', views.subject_detail),
    path('topic/<int:id>', views.topic_detail, name='topic_detail'),
    path('topic/<int:id>/', views.topic_detail),
    path('topic/<int:id>/materials/', views.materials_view, name='topic_materials'),
    path('test/<int:id>/', views.test_take, name='test_take'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    # Teacher routes
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/invite/', views.teacher_invite_student, name='teacher_invite'),
    path('teacher/remove-student/<int:id>/', views.teacher_remove_student, name='teacher_remove_student'),
    # Student routes
    path('student/select-teacher/', views.student_select_teacher, name='student_select_teacher'),
    path('student/leave-teacher/<int:id>/', views.student_leave_teacher, name='student_leave_teacher'),
]



from django.urls import path
from .views import TaskListView, TaskCreateView, TaskUpdateView, TaskDeleteView, about, register, profile, edit_profile, activate_account, CustomLoginView as LoginView, CustomLogoutView as LogoutView, change_language, translate_view

urlpatterns = [
    path('', TaskListView.as_view(), name='task-list'),
    path('create/', TaskCreateView.as_view(), name='task-create'),
    path('<int:pk>/update/', TaskUpdateView.as_view(), name='task-update'),
    path('<int:pk>/delete/', TaskDeleteView.as_view(), name='task-delete'),
    path('about/', about, name='about'),
    path('register/', register, name='register'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit-profile'),
    path('activate/<uuid:token>/', activate_account, name='activate'),
    path('change-language/<str:language_code>/', change_language, name='change_language'),
    path('translate/', translate_view, name='translate'),
]

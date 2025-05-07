<<<<<<< HEAD
<<<<<<< Updated upstream
from django.shortcuts import render
from .models import Task
=======
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Task
from .forms import RegisterForm, UpdateProfileForm, TaskForm
>>>>>>> Stashed changes
=======
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render
from .models import Task
from .forms import TaskForm
>>>>>>> fe2177277daf66f585193d907dca54f526a53eae
import json

class TaskListView(ListView):
    model = Task
    template_name = 'task_list.html'
    context_object_name = 'data'

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_by = self.request.GET.get('sort', '')
        if sort_by == 'price':
            def get_price(item):
                try:
                    if not item.description:
                        return 0
                    details = json.loads(item.description)
                    return float(details.get("price", 0))
                except (json.JSONDecodeError, ValueError, TypeError):
                    return 0
            queryset = sorted(queryset, key=get_price)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        properties_data = []
        for item in context['data']:
            try:
                details = json.loads(item.description) if item.description else {}
            except json.JSONDecodeError:
                details = {}
            prop_dict = {
                "id": item.id,
                "title": item.title,
                "details": details,
                "created_at": item.created_at,
                "image": item.image_url if item.image_url else "https://via.placeholder.com/300x200?text=Нет фото"
            }
            properties_data.append(prop_dict)
        context['data'] = properties_data
        return context

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class TaskCreateView(AdminRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'task_form.html'
    success_url = reverse_lazy('task-list')

class TaskUpdateView(AdminRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'task_form.html'
    success_url = reverse_lazy('task-list')

class TaskDeleteView(AdminRequiredMixin, DeleteView):
    model = Task
    template_name = 'task_confirm_delete.html'
    success_url = reverse_lazy('task-list')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('profile')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                form_html = render_to_string('register.html', {'form': form}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html})
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'login'

@login_required
def profile(request):
    return render(request, 'profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UpdateProfileForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})

def about(request):
    return render(request, 'about.html')
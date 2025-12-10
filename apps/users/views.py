from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView, DetailView, UpdateView, View
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import UserRegisterForm, UserLoginForm, ProfileUpdateForm, UserUpdateForm
from .models import Profile, Role


class RegisterView(SuccessMessageMixin, CreateView):
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    success_message = "Ваш акаунт успішно створено! Тепер ви можете увійти."

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('forum:home')
        return super().dispatch(request, *args, **kwargs)


class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'users/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('forum:home')
        return super().dispatch(request, *args, **kwargs)


class UserLogoutView(LogoutView):
    next_page = 'forum:home'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ProfileView(DetailView):
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['topics'] = user.topics.select_related('category').prefetch_related('posts')[:10]
        context['posts'] = user.posts.select_related('topic')[:10]
        return context


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'users/profile_update.html'
    success_message = "Ваш профіль успішно оновлено!"

    def get_object(self):
        return self.request.user.profile

    def get_success_url(self):
        return reverse_lazy('users:profile', kwargs={'username': self.request.user.username})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['user_form'] = UserUpdateForm(self.request.POST, instance=self.request.user)
        else:
            context['user_form'] = UserUpdateForm(instance=self.request.user)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']

        if user_form.is_valid():
            user_form.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class ToggleBanView(LoginRequiredMixin, View):
    """
    View для блокування/розблокування користувачів
    Доступно тільки для користувачів з правом can_ban_users
    """
    http_method_names = ['post']

    def post(self, request, username):
        # Перевірка прав доступу
        if not request.user.profile.has_permission('can_ban_users'):
            messages.error(request, "У вас немає прав для блокування користувачів.")
            return redirect('forum:home')

        # Отримуємо користувача для блокування
        target_user = get_object_or_404(User, username=username)

        # Не можна заблокувати самого себе
        if target_user == request.user:
            messages.error(request, "Ви не можете заблокувати самого себе.")
            return redirect('users:profile', username=username)

        # Не можна заблокувати власника
        if target_user.profile.role and target_user.profile.role.name == Role.OWNER:
            messages.error(request, "Ви не можете заблокувати власника форуму.")
            return redirect('users:profile', username=username)

        # Перемикаємо стан блокування
        if target_user.profile.is_banned():
            # Розблокувати - призначити роль "Користувач"
            member_role = Role.objects.filter(name=Role.MEMBER).first()
            target_user.profile.role = member_role
            target_user.profile.save()
            messages.success(request, f"Користувача {username} успішно розблоковано.")
        else:
            # Заблокувати - призначити роль "Заблокований"
            banned_role = Role.objects.filter(name=Role.BANNED).first()
            target_user.profile.role = banned_role
            target_user.profile.save()
            messages.success(request, f"Користувача {username} успішно заблоковано.")

        return redirect('users:profile', username=username)

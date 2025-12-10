from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from .models import Category, Topic, Post
from .forms import TopicCreateForm, PostCreateForm


class HomeView(ListView):
    model = Category
    template_name = 'forum/home.html'
    context_object_name = 'categories'

    def get_queryset(self):
        # Показуємо тільки кореневі категорії (без батьківської категорії)
        return Category.objects.filter(parent=None).prefetch_related('subcategories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_topics'] = Topic.objects.select_related('author', 'category').prefetch_related('posts')[:10]
        context['total_topics'] = Topic.objects.count()
        context['total_posts'] = Post.objects.count()
        return context


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'forum/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Теми тільки з поточної категорії (не включаючи підкатегорії)
        context['topics'] = self.object.topics.select_related('author').prefetch_related('posts')
        # Підкатегорії поточної категорії
        context['subcategories'] = self.object.subcategories.all()
        # Breadcrumbs для навігації
        context['breadcrumbs'] = self.object.get_breadcrumbs()
        return context


class TopicDetailView(DetailView):
    model = Topic
    template_name = 'forum/topic_detail.html'
    context_object_name = 'topic'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['posts'] = self.object.posts.select_related('author').all()

        # Показуємо форму тільки якщо користувач не заблокований
        if self.request.user.is_authenticated:
            if not (hasattr(self.request.user, 'profile') and self.request.user.profile.is_banned()):
                context['form'] = PostCreateForm()
        else:
            context['form'] = PostCreateForm()

        # Increment views
        self.object.views += 1
        self.object.save(update_fields=['views'])

        return context


class TopicCreateView(LoginRequiredMixin, CreateView):
    model = Topic
    form_class = TopicCreateForm
    template_name = 'forum/topic_create.html'

    def dispatch(self, request, *args, **kwargs):
        # Перевірка чи не заблокований користувач
        if hasattr(request.user, 'profile') and request.user.profile.is_banned():
            from django.contrib import messages
            messages.error(request, 'Ваш акаунт заблокований. Ви не можете створювати теми.')
            return redirect('forum:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)

        # Create first post with the content from form
        post_content = form.cleaned_data.get('content', '')
        if post_content:
            Post.objects.create(
                topic=self.object,
                author=self.request.user,
                content=post_content
            )

        return response


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostCreateForm
    template_name = 'forum/post_create.html'

    def dispatch(self, request, *args, **kwargs):
        # Перевірка чи не заблокований користувач
        if hasattr(request.user, 'profile') and request.user.profile.is_banned():
            from django.contrib import messages
            messages.error(request, 'Ваш акаунт заблокований. Ви не можете створювати повідомлення.')
            return redirect('forum:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        topic = get_object_or_404(Topic, pk=self.kwargs['topic_pk'])

        if topic.is_closed:
            return redirect('forum:topic_detail', pk=topic.pk)

        form.instance.topic = topic
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.topic.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topic'] = get_object_or_404(Topic, pk=self.kwargs['topic_pk'])
        return context


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostCreateForm
    template_name = 'forum/post_update.html'

    def test_func(self):
        post = self.get_object()
        # Автор поста або користувач з правом редагувати будь-які пости
        if self.request.user == post.author:
            return True
        if hasattr(self.request.user, 'profile') and self.request.user.profile.has_permission('can_edit_any_post'):
            return True
        return False

    def get_success_url(self):
        return self.object.topic.get_absolute_url()


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'forum/post_delete.html'

    def test_func(self):
        post = self.get_object()
        # Автор поста або користувач з правом видаляти будь-які пости
        if self.request.user == post.author:
            return True
        if hasattr(self.request.user, 'profile') and self.request.user.profile.has_permission('can_delete_any_post'):
            return True
        return False

    def get_success_url(self):
        return self.object.topic.get_absolute_url()


class SearchView(ListView):
    model = Topic
    template_name = 'forum/search.html'
    context_object_name = 'topics'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            return Topic.objects.filter(
                Q(title__icontains=query) | Q(posts__content__icontains=query)
            ).distinct().select_related('author', 'category')
        return Topic.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

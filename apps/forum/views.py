from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from .models import Category, Topic, Post, ModerationAction
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

        # Фільтрація топіків за статусом
        user = self.request.user
        recent_topics_qs = Topic.objects.select_related('author', 'category').prefetch_related('posts')

        if user.is_authenticated:
            # Показуємо approved + власні топіки або всі якщо модератор
            if hasattr(user, 'profile') and user.profile.has_permission('can_moderate_topics'):
                # Модератори бачать всі топіки
                recent_topics_qs = recent_topics_qs
            else:
                # Звичайні користувачі бачать approved + свої
                recent_topics_qs = recent_topics_qs.filter(
                    Q(status=Topic.APPROVED) | Q(author=user)
                )
        else:
            # Анонімні користувачі бачать тільки approved
            recent_topics_qs = recent_topics_qs.filter(status=Topic.APPROVED)

        context['recent_topics'] = recent_topics_qs[:10]
        context['total_topics'] = Topic.objects.filter(status=Topic.APPROVED).count()
        context['total_posts'] = Post.objects.count()
        return context


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'forum/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Фільтрація топіків за статусом
        topics_qs = self.object.topics.select_related('author').prefetch_related('posts')

        if user.is_authenticated:
            if hasattr(user, 'profile') and user.profile.has_permission('can_moderate_topics'):
                # Модератори бачать всі топіки
                context['topics'] = topics_qs
            else:
                # Звичайні користувачі бачать approved + свої
                context['topics'] = topics_qs.filter(
                    Q(status=Topic.APPROVED) | Q(author=user)
                )
        else:
            # Анонімні користувачі бачать тільки approved
            context['topics'] = topics_qs.filter(status=Topic.APPROVED)

        # Підкатегорії поточної категорії
        context['subcategories'] = self.object.subcategories.all()
        # Breadcrumbs для навігації
        context['breadcrumbs'] = self.object.get_breadcrumbs()
        return context


class TopicDetailView(DetailView):
    model = Topic
    template_name = 'forum/topic_detail.html'
    context_object_name = 'topic'

    def dispatch(self, request, *args, **kwargs):
        topic = self.get_object()
        user = request.user

        # Перевірка доступу на основі статусу теми
        if topic.status == Topic.APPROVED:
            # Всі можуть переглядати схвалені теми
            pass
        elif topic.status in [Topic.PENDING, Topic.REJECTED]:
            # Тільки автор та модератори можуть переглядати pending/rejected
            if not user.is_authenticated:
                from django.contrib import messages
                messages.error(request, 'Ця тема ще не опублікована.')
                return redirect('forum:home')

            is_author = user == topic.author
            is_moderator = (hasattr(user, 'profile') and
                           user.profile.has_permission('can_moderate_topics'))

            if not (is_author or is_moderator):
                from django.contrib import messages
                messages.error(request, 'Ця тема ще не опублікована.')
                return redirect('forum:home')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['posts'] = self.object.posts.select_related('author').all()

        # Показуємо форму тільки якщо тема схвалена
        if self.object.status == Topic.APPROVED:
            if self.request.user.is_authenticated:
                if not (hasattr(self.request.user, 'profile') and self.request.user.profile.is_banned()):
                    context['form'] = PostCreateForm()
            else:
                context['form'] = PostCreateForm()

        # Інкрементуємо перегляди тільки для схвалених тем
        if self.object.status == Topic.APPROVED:
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
        form.instance.status = Topic.PENDING  # Встановити статус очікування модерації
        response = super().form_valid(form)

        # Create first post with the content from form
        post_content = form.cleaned_data.get('content', '')
        if post_content:
            Post.objects.create(
                topic=self.object,
                author=self.request.user,
                content=post_content
            )

        # Повідомлення для користувача
        from django.contrib import messages
        messages.success(
            self.request,
            'Тему створено! Вона буде опублікована після перевірки модератором.'
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
            topics_qs = Topic.objects.filter(
                Q(title__icontains=query) | Q(posts__content__icontains=query)
            ).distinct().select_related('author', 'category')

            # Фільтрація за статусом
            user = self.request.user
            if user.is_authenticated:
                if hasattr(user, 'profile') and user.profile.has_permission('can_moderate_topics'):
                    return topics_qs
                else:
                    return topics_qs.filter(Q(status=Topic.APPROVED) | Q(author=user))
            else:
                return topics_qs.filter(status=Topic.APPROVED)
        return Topic.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class TopicUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редагування теми (тільки title та category)"""
    model = Topic
    fields = ['title', 'category']
    template_name = 'forum/topic_update.html'

    def test_func(self):
        topic = self.get_object()
        # Тільки автор може редагувати
        if self.request.user != topic.author:
            return False
        # Можна редагувати тільки якщо rejected або pending
        return topic.status in [Topic.REJECTED, Topic.PENDING]

    def dispatch(self, request, *args, **kwargs):
        # Перевірка чи не заблокований
        if hasattr(request.user, 'profile') and request.user.profile.is_banned():
            from django.contrib import messages
            messages.error(request, 'Ваш акаунт заблокований.')
            return redirect('forum:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        from django.contrib import messages
        topic = self.get_object()

        # Якщо тема була відхилена, скидаємо статус на pending
        if topic.status == Topic.REJECTED:
            form.instance.status = Topic.PENDING
            form.instance.moderated_by = None
            form.instance.moderated_at = None
            form.instance.moderation_comment = ''
            messages.success(
                self.request,
                'Тему оновлено та відправлено на повторну модерацію.'
            )
        else:
            messages.success(self.request, 'Тему оновлено.')

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topic'] = self.get_object()
        return context


class ModerationQueueView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Черга модерації для модераторів"""
    model = Topic
    template_name = 'forum/moderation_queue.html'
    context_object_name = 'topics'
    paginate_by = 20

    def test_func(self):
        # Тільки користувачі з правом can_moderate_topics
        if not hasattr(self.request.user, 'profile'):
            return False
        return self.request.user.profile.has_permission('can_moderate_topics')

    def get_queryset(self):
        # Показуємо тільки pending теми
        return Topic.objects.filter(
            status=Topic.PENDING
        ).select_related('author', 'category').prefetch_related('posts').order_by('created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = Topic.objects.filter(status=Topic.PENDING).count()
        return context


class TopicApproveView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Схвалення теми модератором"""
    def test_func(self):
        if not hasattr(self.request.user, 'profile'):
            return False
        return self.request.user.profile.has_permission('can_moderate_topics')

    def post(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)

        # Оновлюємо статус теми
        topic.status = Topic.APPROVED
        topic.moderated_by = request.user
        topic.moderated_at = timezone.now()
        topic.moderation_comment = ''  # Очищаємо попередній коментар
        topic.save()

        # Створюємо запис в історії модерації
        ModerationAction.objects.create(
            topic=topic,
            moderator=request.user,
            action=ModerationAction.APPROVE,
            comment=''
        )

        from django.contrib import messages
        messages.success(request, f'Тему "{topic.title}" схвалено!')

        return redirect('forum:moderation_queue')


class TopicRejectView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Відхилення теми модератором"""
    def test_func(self):
        if not hasattr(self.request.user, 'profile'):
            return False
        return self.request.user.profile.has_permission('can_moderate_topics')

    def post(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)

        # Отримуємо коментар з POST
        comment = request.POST.get('comment', '').strip()
        if not comment:
            from django.contrib import messages
            messages.error(request, 'Будь ласка, вкажіть причину відхилення.')
            return redirect('forum:moderation_queue')

        # Оновлюємо статус теми
        topic.status = Topic.REJECTED
        topic.moderated_by = request.user
        topic.moderated_at = timezone.now()
        topic.moderation_comment = comment
        topic.save()

        # Створюємо запис в історії модерації
        ModerationAction.objects.create(
            topic=topic,
            moderator=request.user,
            action=ModerationAction.REJECT,
            comment=comment
        )

        from django.contrib import messages
        messages.success(request, f'Тему "{topic.title}" відхилено.')

        return redirect('forum:moderation_queue')

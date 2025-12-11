from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва категорії")
    description = models.TextField(blank=True, verbose_name="Опис")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Батьківська категорія"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ['name']
        unique_together = [['name', 'parent']]

    def __str__(self):
        if self.parent:
            return f"{self.parent} → {self.name}"
        return self.name

    def get_absolute_url(self):
        return reverse('forum:category_detail', kwargs={'pk': self.pk})

    def get_breadcrumbs(self):
        """Повертає список категорій від кореневої до поточної"""
        breadcrumbs = [self]
        current = self.parent
        while current:
            breadcrumbs.insert(0, current)
            current = current.parent
        return breadcrumbs

    def get_all_topics(self):
        """Повертає всі теми з поточної категорії та всіх підкатегорій"""
        from django.db.models import Q
        categories = self.get_all_subcategories()
        categories.append(self)
        return Topic.objects.filter(category__in=categories)

    def get_all_subcategories(self):
        """Рекурсивно отримує всі підкатегорії"""
        subcategories = []
        for subcategory in self.subcategories.all():
            subcategories.append(subcategory)
            subcategories.extend(subcategory.get_all_subcategories())
        return subcategories

    def get_level(self):
        """Повертає рівень вкладеності (0 для кореневої категорії)"""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level


class Topic(models.Model):
    # Статуси модерації
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (PENDING, 'Очікує модерації'),
        (APPROVED, 'Схвалено'),
        (REJECTED, 'Відхилено'),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='topics', verbose_name="Категорія")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics', verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    is_pinned = models.BooleanField(default=False, verbose_name="Закріплено")
    is_closed = models.BooleanField(default=False, verbose_name="Закрито")
    views = models.PositiveIntegerField(default=0, verbose_name="Перегляди")

    # Поля модерації
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name="Статус"
    )
    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_topics',
        verbose_name="Модератор"
    )
    moderated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата модерації"
    )
    moderation_comment = models.TextField(
        blank=True,
        verbose_name="Коментар модератора"
    )

    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Теми"
        ordering = ['-is_pinned', '-updated_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('forum:topic_detail', kwargs={'pk': self.pk})

    def get_posts_count(self):
        return self.posts.count()

    def get_last_post(self):
        return self.posts.order_by('-created_at').first()


class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts', verbose_name="Тема")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name="Автор")
    content = CKEditor5Field(verbose_name="Повідомлення", config_name='default')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    class Meta:
        verbose_name = "Повідомлення"
        verbose_name_plural = "Повідомлення"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username} - {self.topic.title[:50]}"

    def get_absolute_url(self):
        return reverse('forum:topic_detail', kwargs={'pk': self.topic.pk})


class ModerationAction(models.Model):
    """Історія дій модерації"""
    APPROVE = 'approve'
    REJECT = 'reject'

    ACTION_CHOICES = [
        (APPROVE, 'Схвалено'),
        (REJECT, 'Відхилено'),
    ]

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='moderation_history',
        verbose_name="Тема"
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='moderation_actions',
        verbose_name="Модератор"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="Дія"
    )
    comment = models.TextField(
        blank=True,
        verbose_name="Коментар"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата дії"
    )

    class Meta:
        verbose_name = "Дія модерації"
        verbose_name_plural = "Дії модерації"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} - {self.topic.title} ({self.moderator.username})"

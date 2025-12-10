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
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='topics', verbose_name="Категорія")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics', verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    is_pinned = models.BooleanField(default=False, verbose_name="Закріплено")
    is_closed = models.BooleanField(default=False, verbose_name="Закрито")
    views = models.PositiveIntegerField(default=0, verbose_name="Перегляди")

    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Теми"
        ordering = ['-is_pinned', '-updated_at']

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

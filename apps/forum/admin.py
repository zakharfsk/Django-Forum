from django.contrib import admin
from django.utils import timezone
from .models import Category, Topic, Post, ModerationAction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['get_hierarchy_name', 'parent', 'subcategories_count', 'topics_count', 'created_at']
    list_filter = ['parent', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['parent__name', 'name']
    list_select_related = ['parent']

    def get_hierarchy_name(self, obj):
        """Показує назву з відступом згідно з рівнем вкладеності"""
        level = obj.get_level()
        indent = '—' * level
        return f"{indent} {obj.name}" if level > 0 else obj.name
    get_hierarchy_name.short_description = 'Назва категорії'

    def subcategories_count(self, obj):
        """Кількість прямих підкатегорій"""
        return obj.subcategories.count()
    subcategories_count.short_description = 'Підкатегорій'

    def topics_count(self, obj):
        """Кількість тем в категорії"""
        return obj.topics.count()
    topics_count.short_description = 'Тем'


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'status', 'moderated_by', 'created_at', 'is_pinned', 'is_closed', 'views']
    list_filter = ['category', 'status', 'is_pinned', 'is_closed', 'created_at']
    search_fields = ['title', 'author__username']
    readonly_fields = ['views', 'created_at', 'updated_at', 'moderated_at']
    ordering = ['-created_at']
    actions = ['pin_topics', 'unpin_topics', 'close_topics', 'open_topics', 'approve_topics', 'reject_topics']

    @admin.action(description='Закріпити теми')
    def pin_topics(self, request, queryset):
        count = queryset.update(is_pinned=True)
        self.message_user(request, f'{count} тем закріплено')

    @admin.action(description='Відкріпити теми')
    def unpin_topics(self, request, queryset):
        count = queryset.update(is_pinned=False)
        self.message_user(request, f'{count} тем відкріплено')

    @admin.action(description='Закрити теми')
    def close_topics(self, request, queryset):
        count = queryset.update(is_closed=True)
        self.message_user(request, f'{count} тем закрито')

    @admin.action(description='Відкрити теми')
    def open_topics(self, request, queryset):
        count = queryset.update(is_closed=False)
        self.message_user(request, f'{count} тем відкрито')

    @admin.action(description='Схвалити теми')
    def approve_topics(self, request, queryset):
        count = queryset.update(
            status=Topic.APPROVED,
            moderated_by=request.user,
            moderated_at=timezone.now()
        )
        # Створити історію модерації для кожної теми
        for topic in queryset:
            ModerationAction.objects.create(
                topic=topic,
                moderator=request.user,
                action=ModerationAction.APPROVE,
                comment='Схвалено через адмін-панель'
            )
        self.message_user(request, f'{count} тем схвалено')

    @admin.action(description='Відхилити теми')
    def reject_topics(self, request, queryset):
        count = queryset.update(
            status=Topic.REJECTED,
            moderated_by=request.user,
            moderated_at=timezone.now(),
            moderation_comment='Відхилено через адмін-панель'
        )
        # Створити історію модерації для кожної теми
        for topic in queryset:
            ModerationAction.objects.create(
                topic=topic,
                moderator=request.user,
                action=ModerationAction.REJECT,
                comment='Відхилено через адмін-панель'
            )
        self.message_user(request, f'{count} тем відхилено')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'created_at']
    list_filter = ['created_at', 'topic__category']
    search_fields = ['content', 'author__username', 'topic__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ['topic', 'moderator', 'action', 'created_at']
    list_filter = ['action', 'created_at', 'moderator']
    search_fields = ['topic__title', 'moderator__username', 'comment']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        # Заборонити ручне створення через адмінку
        return False

    def has_change_permission(self, request, obj=None):
        # Заборонити редагування через адмінку
        return False

from django.contrib import admin
from .models import Category, Topic, Post


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
    list_display = ['title', 'category', 'author', 'created_at', 'is_pinned', 'is_closed', 'views']
    list_filter = ['category', 'is_pinned', 'is_closed', 'created_at']
    search_fields = ['title', 'author__username']
    readonly_fields = ['views', 'created_at', 'updated_at']
    ordering = ['-created_at']
    actions = ['pin_topics', 'unpin_topics', 'close_topics', 'open_topics']

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


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'created_at']
    list_filter = ['created_at', 'topic__category']
    search_fields = ['content', 'author__username', 'topic__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

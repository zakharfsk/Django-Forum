from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'color', 'can_edit_any_post', 'can_delete_any_post', 'can_ban_users']
    list_filter = ['level']
    ordering = ['-level']
    fieldsets = (
        ('Основна інформація', {
            'fields': ('name', 'level', 'color')
        }),
        ('Права доступу', {
            'fields': ('can_edit_any_post', 'can_delete_any_post', 'can_close_topics',
                       'can_pin_topics', 'can_manage_users', 'can_manage_categories', 'can_ban_users')
        }),
    )


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профіль'
    fields = ['role', 'avatar', 'bio', 'location', 'website']


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'location', 'joined_date']
    list_filter = ['role', 'joined_date']
    search_fields = ['user__username', 'location']
    readonly_fields = ['joined_date']
    list_select_related = ['user', 'role']
    actions = ['assign_member_role', 'assign_vip_role', 'assign_moderator_role', 'assign_banned_role']

    @admin.action(description='Призначити роль: Учасник')
    def assign_member_role(self, request, queryset):
        member_role = Role.objects.get(name=Role.MEMBER)
        count = queryset.update(role=member_role)
        self.message_user(request, f'Роль "Учасник" призначена {count} профілям')

    @admin.action(description='Призначити роль: VIP')
    def assign_vip_role(self, request, queryset):
        vip_role = Role.objects.get(name=Role.VIP)
        count = queryset.update(role=vip_role)
        self.message_user(request, f'Роль "VIP" призначена {count} профілям')

    @admin.action(description='Призначити роль: Модератор')
    def assign_moderator_role(self, request, queryset):
        moderator_role = Role.objects.get(name=Role.MODERATOR)
        count = queryset.update(role=moderator_role)
        self.message_user(request, f'Роль "Модератор" призначена {count} профілям')

    @admin.action(description='Заблокувати користувачів')
    def assign_banned_role(self, request, queryset):
        banned_role = Role.objects.get(name=Role.BANNED)
        count = queryset.update(role=banned_role)
        self.message_user(request, f'{count} користувачів заблоковано')

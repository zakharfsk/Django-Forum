from django import template

register = template.Library()


@register.filter
def role_badge(user):
    """
    Повертає HTML badge для ролі користувача
    """
    if not hasattr(user, 'profile') or not user.profile.role:
        return ''

    role = user.profile.role
    role_name = role.get_name_display()

    return f'<span class="badge bg-{role.color} ms-1">{role_name}</span>'


@register.simple_tag
def user_role_badge(user):
    """
    Теж саме що role_badge, але як simple_tag
    """
    if not hasattr(user, 'profile') or not user.profile.role:
        return ''

    role = user.profile.role
    role_name = role.get_name_display()

    return f'<span class="badge bg-{role.color} ms-1">{role_name}</span>'


@register.filter
def has_perm(user, permission):
    """
    Перевіряє чи має користувач певний дозвіл
    Використання: {% if user|has_perm:"can_edit_any_post" %}
    """
    if not hasattr(user, 'profile'):
        return False
    return user.profile.has_permission(permission)

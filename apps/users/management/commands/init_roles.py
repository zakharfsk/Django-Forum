from django.core.management.base import BaseCommand
from apps.users.models import Role


class Command(BaseCommand):
    help = 'Ініціалізація ролей форуму'

    def handle(self, *args, **options):
        roles_config = [
            {
                'name': Role.OWNER,
                'level': 100,
                'color': 'danger',
                'can_edit_any_post': True,
                'can_delete_any_post': True,
                'can_close_topics': True,
                'can_pin_topics': True,
                'can_manage_users': True,
                'can_manage_categories': True,
                'can_ban_users': True,
                'can_moderate_topics': True,
            },
            {
                'name': Role.ADMINISTRATOR,
                'level': 50,
                'color': 'warning',
                'can_edit_any_post': True,
                'can_delete_any_post': True,
                'can_close_topics': True,
                'can_pin_topics': True,
                'can_manage_users': True,
                'can_manage_categories': True,
                'can_ban_users': True,
                'can_moderate_topics': True,
            },
            {
                'name': Role.MODERATOR,
                'level': 30,
                'color': 'success',
                'can_edit_any_post': True,
                'can_delete_any_post': True,
                'can_close_topics': True,
                'can_pin_topics': True,
                'can_manage_users': False,
                'can_manage_categories': False,
                'can_ban_users': True,
                'can_moderate_topics': True,
            },
            {
                'name': Role.VIP,
                'level': 20,
                'color': 'info',
                'can_edit_any_post': False,
                'can_delete_any_post': False,
                'can_close_topics': False,
                'can_pin_topics': False,
                'can_manage_users': False,
                'can_manage_categories': False,
                'can_ban_users': False,
                'can_moderate_topics': False,
            },
            {
                'name': Role.MEMBER,
                'level': 10,
                'color': 'secondary',
                'can_edit_any_post': False,
                'can_delete_any_post': False,
                'can_close_topics': False,
                'can_pin_topics': False,
                'can_manage_users': False,
                'can_manage_categories': False,
                'can_ban_users': False,
                'can_moderate_topics': False,
            },
            {
                'name': Role.BANNED,
                'level': 0,
                'color': 'dark',
                'can_edit_any_post': False,
                'can_delete_any_post': False,
                'can_close_topics': False,
                'can_pin_topics': False,
                'can_manage_users': False,
                'can_manage_categories': False,
                'can_ban_users': False,
                'can_moderate_topics': False,
            },
        ]

        for role_data in roles_config:
            role, created = Role.objects.update_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Створено роль: {role}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Оновлено роль: {role}')
                )

        self.stdout.write(
            self.style.SUCCESS('Ініціалізація ролей завершена!')
        )

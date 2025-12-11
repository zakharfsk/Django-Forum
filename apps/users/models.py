from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_ckeditor_5.fields import CKEditor5Field


class Role(models.Model):
    """Роль користувача на форумі"""
    OWNER = 'owner'
    ADMINISTRATOR = 'administrator'
    MODERATOR = 'moderator'
    VIP = 'vip'
    MEMBER = 'member'
    BANNED = 'banned'

    ROLE_CHOICES = [
        (OWNER, 'Власник'),
        (ADMINISTRATOR, 'Адміністратор'),
        (MODERATOR, 'Модератор'),
        (VIP, 'VIP'),
        (MEMBER, 'Користувач'),
        (BANNED, 'Заблокований'),
    ]

    name = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES, verbose_name="Назва ролі")
    level = models.IntegerField(default=0, verbose_name="Рівень ієрархії")
    color = models.CharField(max_length=20, default='secondary', verbose_name="Колір значка")

    # Права доступу
    can_edit_any_post = models.BooleanField(default=False, verbose_name="Може редагувати будь-які пости")
    can_delete_any_post = models.BooleanField(default=False, verbose_name="Може видаляти будь-які пости")
    can_close_topics = models.BooleanField(default=False, verbose_name="Може закривати теми")
    can_pin_topics = models.BooleanField(default=False, verbose_name="Може закріплювати теми")
    can_manage_users = models.BooleanField(default=False, verbose_name="Може управляти користувачами")
    can_manage_categories = models.BooleanField(default=False, verbose_name="Може управляти категоріями")
    can_ban_users = models.BooleanField(default=False, verbose_name="Може блокувати користувачів")
    can_moderate_topics = models.BooleanField(default=False, verbose_name="Може модерувати теми")

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Ролі"
        ordering = ['-level']

    def __str__(self):
        return self.get_name_display()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Користувач")
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users', verbose_name="Роль")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    bio = CKEditor5Field(blank=True, verbose_name="Про себе", config_name='simple')
    location = models.CharField(max_length=100, blank=True, verbose_name="Місцезнаходження")
    website = models.URLField(blank=True, verbose_name="Веб-сайт")
    joined_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата реєстрації")

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self):
        return f"Профіль {self.user.username}"

    def get_posts_count(self):
        return self.user.posts.count()

    def get_topics_count(self):
        return self.user.topics.count()

    def has_permission(self, permission):
        """Перевірка наявності конкретного права"""
        if not self.role:
            return False
        return getattr(self.role, permission, False)

    def is_staff(self):
        """Чи є користувач персоналом (модератор або вище)"""
        if not self.role:
            return False
        return self.role.level >= 30  # Модератор і вище

    def is_banned(self):
        """Чи заблокований користувач"""
        if not self.role:
            return False
        return self.role.name == Role.BANNED


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Автоматично призначити роль "Користувач" новим користувачам
        default_role = Role.objects.filter(name=Role.MEMBER).first()
        Profile.objects.create(user=instance, role=default_role)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(post_save, sender=Profile)
def update_user_staff_status(sender, instance, **kwargs):
    """
    Автоматично оновлює is_staff та is_superuser для користувачів
    в залежності від їх ролі
    """
    from django.contrib.auth.models import User as UserModel

    user = instance.user
    if instance.role:
        update_needed = False
        new_is_staff = user.is_staff
        new_is_superuser = user.is_superuser

        # Власник отримує superuser права
        if instance.role.name == Role.OWNER:
            if not user.is_superuser or not user.is_staff:
                new_is_superuser = True
                new_is_staff = True
                update_needed = True
        # Адміністратор отримує staff права
        elif instance.role.name == Role.ADMINISTRATOR:
            if not user.is_staff or user.is_superuser:
                new_is_staff = True
                new_is_superuser = False
                update_needed = True
        # Інші ролі не мають доступу до admin
        else:
            if user.is_staff and not user.is_superuser:
                new_is_staff = False
                update_needed = True

        # Використовуємо update щоб уникнути викликання сигналів
        if update_needed:
            UserModel.objects.filter(pk=user.pk).update(
                is_staff=new_is_staff,
                is_superuser=new_is_superuser
            )

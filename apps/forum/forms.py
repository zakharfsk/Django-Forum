from django import forms
from .models import Topic, Post, Category
from django_ckeditor_5.widgets import CKEditor5Widget


class TopicCreateForm(forms.ModelForm):
    content = forms.CharField(
        label='Перше повідомлення (необов\'язково)',
        widget=CKEditor5Widget(config_name='default'),
        required=False
    )

    class Meta:
        model = Topic
        fields = ['title', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть заголовок теми'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Сортуємо категорії для правильного відображення ієрархії
        categories = list(Category.objects.all().order_by('parent__name', 'name'))

        # Створюємо список choices з відступами для візуалізації ієрархії
        category_choices = []
        for category in categories:
            level = category.get_level()
            indent = '—' * level
            label = f"{indent} {category.name}" if level > 0 else category.name
            category_choices.append((category.pk, label))

        self.fields['category'].choices = category_choices


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': CKEditor5Widget(config_name='default')
        }
        labels = {
            'content': 'Повідомлення'
        }

from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('category/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('topic/<int:pk>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('topic/create/', views.TopicCreateView.as_view(), name='topic_create'),
    path('topic/<int:pk>/edit/', views.TopicUpdateView.as_view(), name='topic_update'),
    path('topic/<int:topic_pk>/reply/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_update'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('search/', views.SearchView.as_view(), name='search'),
    # Маршрути модерації
    path('moderation/', views.ModerationQueueView.as_view(), name='moderation_queue'),
    path('moderation/topic/<int:pk>/approve/', views.TopicApproveView.as_view(), name='topic_approve'),
    path('moderation/topic/<int:pk>/reject/', views.TopicRejectView.as_view(), name='topic_reject'),
]

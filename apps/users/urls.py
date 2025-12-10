from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/<str:username>/toggle-ban/', views.ToggleBanView.as_view(), name='toggle_ban'),
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
]


from django.urls import path
from . import views

urlpatterns = [
    # HTML Views
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
    
    # API Views
    path('api/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('api/profile/', views.ProfileAPIView.as_view(), name='api_profile'),
]

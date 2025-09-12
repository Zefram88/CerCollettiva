from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/complete/', views.profile_complete, name='profile_complete'),
    path('login/', views.login_view, name='login'),
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/<int:pk>/', views.AdminUserProfileView.as_view(), name='admin_profile'),  # profilo di altri utenti (admin only)
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('delete_account/', views.DeleteAccountView.as_view(), name='delete_account'),
    path('detail/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),

    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        success_url='/users/password_reset/done/',
        email_template_name='users/password_reset_email.html'
    ), name='password_reset'),
    
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url='/users/reset/done/'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    path('management/', views.UserManagementView.as_view(), name='management'),

]
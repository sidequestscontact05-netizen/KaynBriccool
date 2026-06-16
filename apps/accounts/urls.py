from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView, PasswordResetDoneView, PasswordResetCompleteView
from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_choice, name='register'),
    path('register/client/', views.ClientRegisterView.as_view(), name='register_client'),
    path('register/tasker/', views.TaskerRegisterView.as_view(), name='register_tasker'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('verify-phone/', views.VerifyPhoneView.as_view(), name='verify_phone'),
    path('verify-phone/resend/', views.ResendCodeView.as_view(), name='resend_code'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('verify-email/resend/', views.ResendEmailCodeView.as_view(), name='resend_email_code'),
    path('verify-face/', views.VerifyFaceIdView.as_view(), name='verify_face'),
    path('forgot-password/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('forgot-password/done/', PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('tasker/<int:tasker_id>/', views.tasker_profile, name='tasker_profile'),
    path('switch-role/', views.switch_role, name='switch_role'),
    path('become-tasker/', views.become_tasker, name='become_tasker'),
    path('become-client/', views.become_client, name='become_client'),
    path('onboarding/done/', views.onboarding_done, name='onboarding_done'),
    path('welcome/dismiss/', views.dismiss_welcome_modal, name='dismiss_welcome_modal'),
    path('social/complete/', views.social_complete, name='social_complete'),
    path('firebase/login/', views.FirebaseLoginView.as_view(), name='firebase_login'),
]

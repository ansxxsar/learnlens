from django.urls import path

from .views import (
    ChangePasswordView,
    CsrfView,
    MeView,
    ProfilePhotoView,
    RegisterView,
    SignInView,
    SignOutView,
)

urlpatterns = [
    path('csrf', CsrfView.as_view(), name='auth-csrf'),
    path('sign-in', SignInView.as_view(), name='auth-sign-in'),
    path('register', RegisterView.as_view(), name='auth-register'),
    path('sign-out', SignOutView.as_view(), name='auth-sign-out'),
    path('me', MeView.as_view(), name='auth-me'),
    path('me/photo', ProfilePhotoView.as_view(), name='auth-photo'),
    path('change-password', ChangePasswordView.as_view(), name='auth-change-password'),
]

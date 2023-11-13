from django.urls import path
from core.views.app import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', home, name='home'),
    path('password_reset/', password_reset,
        name='password_reset'),
    path('password_reset/done/',
        password_reset_done, name='password_reset_done'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),
    path('confirm/', password_confirm, name="confirm"),
    path('password/set/', reset_confirm, name="reset_confirm")

]

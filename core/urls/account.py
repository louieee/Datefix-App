from django.urls import path
from core.views.account import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', login, name='login'),
    path('signup/', signup, name='signup'),
    path('dashboard/', dashboard, name='dashboard'),
    path('results/', results, name='results'),
    path('account/not_found/', not_found, name='not_found'),
    path('account/verify/', verify, name="verify"),
    path('account/verified/', verified, name='verified'),
    path('account/send_verify/', verification, name='verification'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),
    path('personality_test/', personality_test, name="personality_test"),
    path('personality_test/result/', test_result, name="test_result"),
    path('logout/', logout, name='logout')

]

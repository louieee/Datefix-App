from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views
from Datefix.views import password_reset_done, password_reset, password_confirm, reset_confirm
urlpatterns = [
    path('login/', login, name='login'),
    path('signup/', signup, name='signup'),
    path('dashboard/', dashboard, name='dashboard'),
    path('match/', matching, name='match'),
    path('results/', results, name='results'),
    path('account/not_found/', not_found, name='not_found'),
    path('account/verify/', verify, name="verify"),
    path('account/verified/', verified, name='verified'),
    path('account/send_verify/', verification, name='verification'),
    path('password_reset/', password_reset,
        name='password_reset'),
    path('password_reset/done/',
        password_reset_done, name='password_reset_done'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),
    path('get_data/<type_>/', get_data, name="get_data"),
    path('personality_test/', personality_test, name="personality_test"),
    path('personality_test/submit/', personality, name='submit_test'),
    path('personality_test/result/', test_result, name="test_result"),
    path('logout/', logout, name='logout'),
    path('api/get_couple/<int:couple_id>/', get_couple, name="get_couple"),
    path('confirm/', password_confirm, name="confirm"),
    path('password/set/', reset_confirm, name="reset_confirm")

]

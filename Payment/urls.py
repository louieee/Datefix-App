from django.urls import path
from .views import *

urlpatterns = [
    path('redirect/', redirect_match, name='redirect_match'),
    path('rave/redirect/<int:user_id>/<package>/<duration>/<tx_ref>/', rave_redirect, name='rave_redirect'),
    path('rave/webhook/', rave_webhook, name='rave_webhook'),
    path('pay/', rave_pay, name='pay'),
    ]


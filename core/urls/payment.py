from django.urls import path
from core.views import payment

urlpatterns = [
	path('redirect/', payment.redirect_match, name='redirect_match'),
	path('rave/redirect/<int:user_id>/<package>/<duration>/<tx_ref>/', payment.rave_redirect, name='rave_redirect'),
	path('rave/webhook/', payment.rave_webhook, name='rave_webhook'),
	path('pay/', payment.rave_pay, name='pay'),
	]


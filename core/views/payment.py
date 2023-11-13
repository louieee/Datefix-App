from datetime import timedelta

from django.shortcuts import render, redirect
from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.models import User, Payment
from core.services.ravepay_services import RavePayServices


@login_required(login_url='login')
def redirect_match(request):
	user = User.objects.get(id=request.user.id)
	user.update_matchability()
	if user.can_be_matched:
		return render(request, 'Payment/match.html')
	else:
		return redirect('personality_test')


@csrf_exempt
@require_POST
def rave_webhook(request):
	rave_secret = request.headers.get("verify-hash")
	data = request.POST
	rave = RavePayServices({})
	try:
		payment_ = Payment.objects.get(tx_ref__exact=data['txRef'])
	except Payment.DoesNotExist:
		return
	if payment_ is not None:
		my_secret = config('RAVE_PAY_KEY')
		if rave_secret != my_secret or data['status'] != 'successful' or \
				data['currency'] != 'NGN' or data['amount'] < rave.package_price(payment_.package, payment_.duration) \
				or payment_.payer_id != data['customer']['id']:
			payment_.status = 'FAILED'
			return HttpResponse('****')
		payment_.status = 'PAID'
		if payment_.duration == 'QUARTERLY':
			payment_.expiry_date = payment_.date_of_payment.astimezone() + timedelta(days=90)
		if payment_.duration == 'YEARLY':
			payment_.expiry_date = payment_.date_of_payment.astimezone() + timedelta(days=365)
		payment_.save()
		user = User.objects.get(id=payment_.payer_id)
		user.can_be_matched = True
		if payment_.package == 'REGULAR':
			user.extra_support = False
		if payment_.package == 'PREMIUM':
			user.extra_support = True
		user.save()
		return HttpResponse('**ok**')


@login_required(login_url='login')
def rave_redirect(request, user_id, package, duration, tx_ref):
	try:
		Payment.objects.get(tx_ref__exact=tx_ref)
	except Payment.DoesNotExist:
		payment = Payment.objects.create(payer_id=user_id, package=str(package).upper(),
										 duration=str(duration).upper(), tx_ref=tx_ref)
		payment.save()

		# we are doing this for test sake

		payment.status = 'PAID'
		if payment.duration == 'QUARTERLY':
			payment.expiry_date = payment.date_of_payment + timedelta(days=90)
		if payment.duration == 'YEARLY':
			payment.expiry_date = payment.date_of_payment + timedelta(days=365)
		payment.save()
		user = User.objects.get(id=payment.payer_id)
		user.can_be_matched = True
		if payment.package == 'REGULAR':
			user.extra_support = False
		if payment.package == 'PREMIUM':
			user.extra_support = True
		user.save()

	# ends here

	return render(request, 'Payment/rave_redirect.html')


@login_required(login_url='login')
def rave_pay(request):
	user = User.objects.get(id=request.user.id)
	if request.method == 'GET':
		if user.update_matchability():
			return redirect('redirect_match')
		else:
			return render(request, 'Payment/pay.html')
	if request.method == 'POST':
		if user.can_be_matched:
			return redirect('redirect_match')
		data = {}
		if 'REGULAR' in request.POST:
			data["package"] = "REGULAR"
		if 'PREMIUM' in request.POST:
			data["package"] = "PREMIUM"
		if 'duration' in request.POST:
			data["duration"] = "YEARLY"
		else:
			data["duration"] = "QUARTERLY"
		data['user_id'] = request.user.id
		rave = RavePayServices(data)
		executed = rave.make_payment()
		if executed:
			return redirect(rave.link)
		return redirect('pay')

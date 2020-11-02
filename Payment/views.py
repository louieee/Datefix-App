import django.shortcuts
from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from Account.models import User
from Payment.algorithm import can_be_matched
from services.ravepay_services import RavePayServices
from .models import Payment


@login_required()
def redirect_match(request):
    if can_be_matched(request.user.id):
        return django.shortcuts.render(request, 'Payment/match.html')
    else:
        return django.shortcuts.redirect('personality_test')


@csrf_exempt
@require_POST
def rave_webhook(request):
    rave_secret = request.headers.get("verify-hash")
    data = request.POST
    rave = RavePayServices({})
    payment_ = None
    try:
        payment_ = Payment.objects.get(tx_ref__exact=data['txRef'])
    except Payment.DoesNotExist:
        return
    if payment_ is not None:
        my_secret = config('RAVE_PAY_KEY')
        if rave_secret != my_secret or data['status'] != 'successful' or \
                data['currency'] != 'NGN' or data['amount'] < rave.package_price(payment_.package) \
                or payment_.payer_id != data['customer']['id']:
            payment_.status = 'FAILED'
            return HttpResponse('****')
        payment_.status = 'PAID'
        payment_.save()
        user = Payment.payer
        user.can_be_matched = True
        if payment_.package == 'REGULAR':
            user.extra_support = False
        if payment_.package == 'PREMIUM':
            user.extra_support = True
        user.save()
        return HttpResponse('**ok**')


@login_required()
def rave_redirect(request, user_id, package, duration, tx_ref):
    from datetime import timedelta
    user = User.objects.get(id=user_id)
    try:
        Payment.objects.get(tx_ref__exact=tx_ref)
    except Payment.DoesNotExist:
        payment = Payment.objects.create(payer_id=user_id, package=str(package).upper(),
                                         duration=str(duration).upper(), tx_ref=tx_ref)
        if payment.duration == 'QUARTERLY':
            payment.expiry_date = payment.date_of_payment.astimezone() + timedelta(days=90)
        if payment.duration == 'YEARLY':
            payment.expiry_date = payment.date_of_payment.astimezone() + timedelta(days=365)
        payment.save()
    return django.shortcuts.render(request, 'Payment/rave_redirect.html')


@login_required()
def rave_pay(request):
    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        if can_be_matched(user.id):
            return django.shortcuts.redirect('redirect_match')
        else:
            return django.shortcuts.render(request, 'Payment/pay.html')
    if request.method == 'POST':
        if user.can_be_matched:
            return django.shortcuts.redirect('redirect_match')
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
            return django.shortcuts.redirect(rave.link)
        return django.shortcuts.redirect('pay')

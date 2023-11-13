import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from core.helpers.utilities import get_personality, get_score, purify_email
from core.models import User, PersonalityTest, Couple


@csrf_exempt
def personality(request):
	if request.method == 'GET':
		data = request.GET
		user = None
		score = int(data['score'])
		if 'email' not in request.session:
			request.session['email'] = purify_email(data['email'])
		test, _ = PersonalityTest.objects.get_or_create(email=purify_email(data['email']))
		if request.user.is_authenticated and 'is_user' not in request.session and data['email'] == request.user.email:
			user = request.user
			request.session['is_user'] = True
		if user is not None:
			user_data = user.user_data
			user_data[data['category'].lower()] = get_score(score)
			user.user_data = user_data
			user.save()

		if data['category'] == 'Extraversion':
			request.session['category'] = 'Neurotism'
			test.extraversion = get_personality(score, data['category'])

		if data['category'] == 'Neurotism':
			request.session['category'] = 'Agreeableness'
			test.neurotism = get_personality(score, data['category'])

		if data['category'] == 'Agreeableness':
			request.session['category'] = 'Conscientiousness'
			test.agreeableness = get_personality(score, data['category'])

		if data['category'] == 'Conscientiousness':
			request.session['category'] = 'Openness'
			test.conscientiousness = get_personality(score, data['category'])

		if data['category'] == 'Openness':
			request.session['category'] = 'End'
			test.openness = get_personality(score, data['category'])
			test.save()
			return HttpResponse('Finished')
		test.save()
		return HttpResponse('Remaining')


def get_user(request, user_id):
	if request.method == 'GET':
		user = User.objects.get(id=user_id)
		return HttpResponse(json.dumps(user.serialized_data))


# verified
def matching(request):
	if request.method == 'GET':
		user = User.objects.get(id=request.user.id)
		if user.sex == 'female':
			user.match_user()
		return HttpResponse('success')


# verified
def get_data(request, type_):
	if request.method == 'GET':
		data = {key: request.GET[key] for key in request.GET.keys()}
		user = User.objects.get(id=request.user.id)
		if type_ == 'user':
			user_data = user.user_data
			user_data.update(data)
			user.user_data = user_data
			user.save()
			return HttpResponse('success')

		if type_ == 'partner':
			if request.GET['residence_state'] == '' and request.GET['origin_state'] == '':
				return HttpResponse('success')
			user_data = user.choice_data
			user_data.update(data)
			user.deal_breaker = [user_data['dealbreaker1'], user_data['dealbreaker2']]
			del (user_data['dealbreaker1'], user_data['dealbreaker2'])
			user.choice_data = user_data
			user.save()
			return HttpResponse('success')

		return HttpResponse('fail')


@csrf_exempt
@login_required(login_url='login')
def decrypt(request):
	if request.method == 'POST':
		user = User.objects.get(id=request.user.id)
		data = {"status": 200, "message": user.decrypt(request.POST['message'].encode())}
		return JsonResponse(data)
	return JsonResponse({"status": 400, "message": "Bad Request"})


@csrf_exempt
@login_required(login_url='login')
def encrypt(request):
	if request.method == 'POST':
		user = User.objects.get(id=request.user.id)
		data = {"status": 200, "message": user.encrypt(request.POST['message']).decode()}
		return JsonResponse(data)
	return JsonResponse({"status": 400, "message": "Bad Request"})


def get_couple(request, couple_id):
	try:
		couple = Couple.objects.get(id=couple_id)
		if couple.first_partner_id == request.user.id or couple.second_partner_id == request.user.id:
			return HttpResponse(json.dumps(couple.true_details(request.user.id)))
		return HttpResponse('You are not yet a couple')
	except Couple.DoesNotExist:
		return HttpResponse('No Couple exists with this ID.')

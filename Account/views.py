from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponse
from django.contrib import auth
from django.views.decorators.csrf import csrf_exempt
from .models import User, PersonalityTest, Couple
import json
from .algorithms import match_user, flash, display, send_verification, get_username, get_personality, get_score
from Chat.algorithms import create_chat


# Create your views here.

# login function verified
def login(request):
	if request.method == 'POST':
		if not request.POST.get('email', False) or not request.POST.get('password', False):
			flash(request, 'No login details was entered !', 'danger', 'remove-sign')
			return redirect('login')
		email = str(request.POST['email']).lower()
		try:
			user = User.objects.get(email=email)

			if not user.verified:
				request.session['email'] = user.email
				send_verification(request, user)
				return redirect('verification')

			user = auth.authenticate(
				request, username=email, password=request.POST['password'])
			if user is None:
				flash(request, 'Password Incorrect !', 'danger', 'remove-sign')
				return redirect('login')
			if user is not None:
				auth.login(request, user)
				flash(request, f'{user.username} is logged in successfully !', 'success', 'thumbs-up')
				user.status = 'Online'
				user.save()
				return redirect('dashboard')
		except User.DoesNotExist:
			flash(request, 'There is no Account with this email address !', 'info', 'info-sign')
			return redirect('not_found')

	if request.method == 'GET':
		if request.user.is_authenticated:
			if 'email' in request.session:
				del request.session['email']
			return redirect('dashboard')
		flash_ = display(request)
		if flash_ is None:
			return render(request, 'Account/login.html')
		return render(request, 'Account/login.html', {'message': flash_[0], 'status': flash_[1], "icon": flash_[2]})


@login_required
def logout(request):
	user = User.objects.get(id=request.user.id)
	from datetime import datetime
	user.status = f"Last seen at {datetime.now().time().strftime('%I:%M %p')} " \
				  f"on {datetime.now().date().strftime('%e - %b - %Y')}."
	user.save()
	auth.logout(request)
	if '_logout' in request.session:
		del request.session['_logout']
		return HttpResponse('ok')
	return redirect('home')


@csrf_exempt
def personality(request):
	if request.method == 'GET':
		user = None
		score = int(request.GET['score'])
		if 'email' not in request.session:
			request.session['email'] = request.GET['email']
		test_ = PersonalityTest()
		try:
			test_ = PersonalityTest.objects.get(email=request.GET['email'])
		except PersonalityTest.DoesNotExist:
			test_.email = request.GET['email']

		if request.user.is_authenticated and 'is_user' not in request.session:
			if request.user.email == request.GET['email']:
				user = User.objects.get(id=request.user.id)
				request.session['is_user'] = True

		if user is not None:
			data = user.user_data_()
			data[str(request.GET['category']).lower()] = get_score(score)
			user.user_data = json.dumps(data)
			user.save()

		if request.GET['category'] == 'Extraversion':
			request.session['category'] = 'Neurotism'
			test_.extraversion = get_personality(score, request.GET['category'])

		if request.GET['category'] == 'Neurotism':
			request.session['category'] = 'Agreeableness'
			test_.neurotism = get_personality(score, request.GET['category'])

		if request.GET['category'] == 'Agreeableness':
			request.session['category'] = 'Conscientiousness'
			test_.agreeableness = get_personality(score, request.GET['category'])

		if request.GET['category'] == 'Conscientiousness':
			request.session['category'] = 'Openness'
			test_.conscientiousness = get_personality(score, request.GET['category'])

		if request.GET['category'] == 'Openness':
			request.session['category'] = 'End'
			test_.openness = get_personality(score, request.GET['category'])
			test_.save()

			return HttpResponse('Finished')
		test_.save()
		return HttpResponse('Remaining')


# verified
def results(request):
	user = User.objects.get(id=request.user.id)
	if request.method == 'GET':
		if user.sex == 'female':
			show = display(request)
			matches = user.successful_list()[:6]
			size = len(matches)
			select = [(x[0], User.objects.get(id=x[0]).username) for x in matches]
			matches = ((User.objects.get(id=x[0]), x[1]) for x in matches)
			matches = ((
				(str(x[0].id), x[1]),
				("alpha", x[0].username),
				("Origin", x[0].user_data_()['origin_state']),
				["Residence", x[0].user_data_()['residence_state']],
				("Religion", x[0].user_data_()['religion']),
				("denomination", x[0].user_data_()['denomination']),
				("Has Children", x[0].user_data_()['children']))
				for x in matches)
			if show is None:
				return render(request, 'Account/results.html',
							  {'matches': matches, "select": select, "matches_length": size})
			else:
				return render(request, 'Account/results.html',
							  {'matches': matches, "select": select, "matches_length": size, "message": show[0],
							   "status": show[1], "icon": show[2]})

		if user.sex == 'male':
			matches = (User.objects.get(id=x) for x in user.matches_())
			return render(request, 'Account/results_m.html',
						  {'matches': matches, "matches_length": len(user.matches_())})

	if request.method == 'POST':
		match_1 = int(request.POST['match1'])
		match_2 = int(request.POST['match2'])
		if match_1 == match_2:
			flash(request, 'The selected users are the same. please select different users.', 'danger', 'remove-icon')
			return redirect('results')
		user.matches = json.dumps([int(x) for x in (match_1, match_2)])
		user.session = 2
		user.save()
		match_comp = tuple([str(x) for x in (match_1, match_2) if User.objects.get(id=int(x)).complete_match()])
		verb = ''
		if len(match_comp) > 0:
			if len(match_comp) == 2:
				verb = 'has'
			if len(match_comp) == 1:
				verb = 'have'
			request.session['message'] = f'{"and ".join(match_comp)} {verb} complete matches, so choose another.'
			request.session['status'] = 'danger'
			request.session['icon'] = 'remove-icon'
			return redirect('results')
		if len(match_comp) == 0:
			add_new(request, user, match_1)
			add_new(request, user, match_2)
			return redirect('chatroom')


def add_new(request, user, id_):
	success = user.successful_list()
	success = tuple([x for x in success if x[0] != int(id_)])
	user.successful_matches = json.dumps(success)
	user.save()
	create_chat(request, user.id, int(id_))


# signup verified
def signup(request):
	if request.method == 'POST':
		if not (request.POST['password1'] == request.POST['password2'] and request.POST['password1'] != ''):
			flash(request, 'The passwords are not equal !', 'danger', 'remove-sign')
			return redirect('login')

		if not request.POST.get('email', False) or not request.POST.get('last-name', False) or not request.POST.get(
				'first-name', False):
			flash(request, 'Some Fields are empty !', 'danger', 'remove-sign')
			return redirect('login')
		email = str(request.POST['email']).lower()
		user = User.objects.filter(email=email).first()
		if user is not None:
			flash(request, 'This email already exists !', 'danger', 'remove-sign')
			return redirect('login')
		from Datefix.algorithms import get_key
		username = get_username()
		user = User.objects.create_user(
			username=username,
			email=email,
			password=request.POST['password1'],
			first_name=request.POST['first-name'],
			last_name=request.POST['last-name'],
			sex=request.POST['sex'],
			phone=request.POST['phone']
		)
		user.save()
		flash(request, f"{request.POST['first-name']}, your account has been "
					   f"created successfully.", 'success', 'thumbs-up')
		request.session['email'] = user.email
		send_verification(request, user)
		return redirect('verification')
	if request.method == 'GET':
		if request.user.is_authenticated:
			return redirect('dashboard')
		flash_ = display(request)
		if flash_ is None:
			return render(request, 'Account/login.html')
		return render(request, 'Account/login.html', {'message': flash_[0], 'status': flash_[1], 'icon': flash_[2]})


# verified
def dashboard(request):
	if request.method == 'GET':
		if not request.user.is_authenticated:
			return redirect('login')

		user = User.objects.get(id=request.user.id)

		if user.session is not -1 and user.can_be_matched:
			return redirect('chatroom')
		else:
			if user.complete_match() and user.can_be_matched:
				return redirect('chatroom')

			if user.user_data == '{}':
				return render(request, 'Account/profile.html')

			if user.choice_data == '{}':
				user_details = user.user_data_()
				user_details['registered'] = True
				return render(request, 'Account/profile.html', user_details)

			if user.sex == 'male' and not user.complete_match() and user.can_be_matched:
				return redirect('results')

			if user.sex == 'female' and not user.complete_match():
				user_details = user.user_data_()
				user_details['registered'] = True
				return render(request, 'Account/profile.html', user_details)

			return redirect('home')


# verified
def matching(request):
	if request.method == 'GET':
		user = User.objects.get(id=request.user.id)
		if user.sex == 'female':
			match_user(user)
		return HttpResponse('success')


# verified
def get_data(request, type_):
	if request.method == 'GET':
		user = User.objects.get(id=request.user.id)
		if type_ == 'user':
			user_data = json.loads(user.user_data)
			user_data.update(request.GET)
			user.user_data = json.dumps(user_data).replace(
				']', '').replace('[', '')
			user.save()
			return HttpResponse('success')

		if type_ == 'partner':
			user_data = json.loads(user.choice_data)
			if request.GET['residence_state'] == '' and request.GET['origin_state'] == '':
				return HttpResponse('success')

			user_data.update(request.GET)
			user.deal_breaker = f"[{json.dumps([user_data['dealbreaker1'], user_data['dealbreaker2']]).replace(']', '').replace('[', '')}]"
			del (user_data['dealbreaker1'], user_data['dealbreaker2'])
			user.choice_data = json.dumps(
				user_data).replace(']', '').replace('[', '')
			user.save()
			return HttpResponse('success')

		return HttpResponse('fail')


# verified
def verified(request):
	if 'email' in request.session and request.session['verified'] is True:
		user = User.objects.get(email=request.session['email'])
		user.verified = True
		user.save()
		auth.login(request, user, backend='django.contrib.auth.backends.ModelBackend')
		flash(request, f'{user.username} is logged in successfully !', 'success', 'thumbs-up')
		user.status = 'Online'
	return render(request, 'Account/account-verified.html')


# verify function is verified
def verify(request):
	if request.method == 'POST':
		flash(request, 'Invalid Request !', 'danger')
		return redirect('login')

	if 'code' not in request.session:
		if 'verification_sent' in request.session:
			del request.session['verification_sent']
		flash(request, 'Code has expired !', 'danger', 'remove-sign')
		return redirect('login')

	del request.session['code']
	request.session['verified'] = True
	request.session['email'] = request.GET['email']
	return redirect('verified')


# verified
def not_found(request):
	return render(request, 'Account/account-not-found.html')


# verified
def verification(request):
	return render(request, 'Account/verification-link-sent.html', {"email": request.session['email']})


# verified
def personality_test(request):
	from .algorithms import dict_to_zip
	data = None
	email = ''
	if request.user.is_authenticated:
		email = request.user.email

	if 'category' not in request.session:
		from .algorithms import category_1
		data = dict_to_zip(category_1)
		category = 'Extraversion'

	else:
		category = request.session['category']
		if category == 'Neurotism':
			from .algorithms import category_2
			data = dict_to_zip(category_2)
		if category == 'Agreeableness':
			from .algorithms import category_3
			data = dict_to_zip(category_3)
		if category == 'Conscientiousness':
			from .algorithms import category_4
			data = dict_to_zip(category_4)
		if category == 'Openness':
			from .algorithms import category_5
			data = dict_to_zip(category_5)
		email = request.session['email']

	return render(request, 'Account/test.html', {'email': email, 'data': data, 'category': category})


def test_result(request):
	if request.method == 'GET':
		from .algorithms import categories
		try:
			your_personality = PersonalityTest.objects.get(email=request.session['email'])
			data = zip(
				categories,
				(
					json.loads(your_personality.extraversion)['title'],
					json.loads(your_personality.neurotism)['title'],
					json.loads(your_personality.agreeableness)['title'],
					json.loads(your_personality.conscientiousness)['title'],
					json.loads(your_personality.openness)['title']
				),
				(
					json.loads(your_personality.extraversion)['description'],
					json.loads(your_personality.neurotism)['description'],
					json.loads(your_personality.agreeableness)['description'],
					json.loads(your_personality.conscientiousness)['description'],
					json.loads(your_personality.openness)['description'],
				)
			)
			return render(request, 'Account/personality_result.html', {'data': data,
																	   "email": request.session['email'].split('@')[0]})
		except (PersonalityTest.DoesNotExist, KeyError):
			return redirect('personality_test')

	if request.method == 'POST':
		del request.session['category'], request.session['email']
		return redirect('personality_test')


@csrf_exempt
@login_required
def decrypt(request):
	if request.method == 'POST':
		user = User.objects.get(id=request.user.id)
		data = {"status": 200, "message": user.decrypt(request.POST['message'].encode())}
		return JsonResponse(data)
	return JsonResponse({"status": 400, "message": "Bad Request"})


@csrf_exempt
@login_required
def encrypt(request):
	if request.method == 'POST':
		user = User.objects.get(id=request.user.id)
		data = {"status": 200, "message": user.encrypt(request.POST['message']).decode()}
		return JsonResponse(data)
	return JsonResponse({"status": 400, "message": "Bad Request"})


def encrypt_(message):
	user = User.objects.get(id=3)
	data = {"status": 200, "message": user.encrypt(message).decode()}
	return JsonResponse(data)


def decrypt_(message):
	user = User.objects.get(id=3)
	data = {"status": 200, "message": user.decrypt(message.encode())}
	return JsonResponse(data)


def get_couple(request, couple_id):
	try:
		couple = Couple.objects.get(id=couple_id)
		if couple.first_partner_id == request.user.id or couple.second_partner_id == request.user.id:
			return HttpResponse(json.dumps(couple.true_details(request.user.id)))
		return HttpResponse('You are not yet a couple')
	except Couple.DoesNotExist:
		return HttpResponse('No Couple exists with this ID.')

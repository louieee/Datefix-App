from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponse
from django.contrib import auth
from django.views.decorators.csrf import csrf_exempt
from .models import User, PersonalityTest, Couple
import json
from .utils import match_user, flash, display, send_verification, get_username, get_personality, get_score
from Chat.utils import create_chat, purify_email


# Create your views here.

# login function verified
def login(request):
    if request.method == 'POST':
        data = request.POST
        if "email" not in data and "password" not in data:
            flash(request, 'No login details was entered !', 'danger', 'remove-sign')
            return redirect('login')
        email = purify_email(data['email'])
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            flash(request, 'There is no Account with this email address !', 'info', 'info-sign')
            return redirect('not_found')
        if not user.verified:
            request.session['email'] = user.email
            send_verification(request, user)
            return redirect('verification')
        user = auth.authenticate(
            request, username=email, password=data['password'])
        if user is None:
            flash(request, 'Password Incorrect!', 'danger', 'remove-sign')
            return redirect('login')
        auth.login(request, user)
        flash(request, f'Welcome {user.username}!', 'success', 'thumbs-up')
        user.status = 'Online'
        # send ws here to notify other users
        user.save()
        return redirect('dashboard')

    if request.method == 'GET':
        if request.user.is_authenticated:
            if 'email' in request.session:
                del request.session['email']
            return redirect('dashboard')
        flash_ = display(request)
        if flash_ is None:
            return render(request, 'Account/login.html')
        return render(request, 'Account/login.html', {'message': flash_[0], 'status': flash_[1], "icon": flash_[2]})


@login_required(login_url='login')
def logout(request):
    user = User.objects.get(id=request.user.id)
    from datetime import datetime
    user.status = f"Last seen at {datetime.now().time().strftime('%I:%M %p')} " \
                  f"on {datetime.now().date().strftime('%e - %b - %Y')}."
    # send ws here
    user.save()
    auth.logout(request)
    if '_logout' in request.session:
        del request.session['_logout']
        return HttpResponse('ok')
    return redirect('home')


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


# verified
def results(request):
    from Chat.models import ChatThread
    user = User.objects.get(id=request.user.id)

    if request.method == 'GET':
        match_user(user)
        show = display(request)
        matches = user.successful_matches[:6]
        size = len(matches)
        match_dict = {x[0]: x[1] for x in matches}
        select_users = User.objects.filter(id__in=(x[0] for x in matches)).only("id", "username", "user_data")
        matches = ((
            (user.id, match_dict[user.id]),
            ("alpha", user.username),
            ("Origin", user.user_data['origin_state']),
            ["Residence", user.user_data['residence_state']],
            ("Religion", user.user_data['religion']),
            ("denomination", user.user_data['denomination']),
            ("Has Children", user.user_data['children']))
            for user in select_users)
        if show is None:
            return render(request, 'Account/results.html',
                          {'matches': matches, "select": select_users.values_list("id", "username"),
                           "matches_length": size})
        else:
            return render(request, 'Account/results.html',
                          {'matches': matches, "select": select_users.values_list("id", "username"),
                           "matches_length": size, "message": show[0],
                           "status": show[1], "icon": show[2]})

    elif request.method == 'POST':
        match_1 = int(request.POST['match1'])
        match_2 = int(request.POST['match2'])
        matches = [match_1, match_2]
        if match_1 == match_2:
            matches = [match_1]
        user.matches = matches
        user.save()
        for user_id in matches:
            create_new_chat(user, user_id)
        return redirect('chatroom')
    else:
        flash(request, "Invalid Request", "danger")


def create_new_chat(user, id_):
    success = user.successful_matches
    success = [x for x in success if x[0] != int(id_)]
    user.successful_matches = success
    user.save()
    create_chat(user.id, int(id_))
    return


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
        email = purify_email(str(request.POST['email']))
        user = User.objects.filter(email=email).first()
        if user is not None:
            flash(request, 'This email already exists !', 'danger', 'remove-sign')
            return redirect('login')
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
        if user.user_data == dict():
            return render(request, 'Account/profile.html')
        if user.choice_data == dict():
            user_details = user.user_data
            user_details['registered'] = True
            return render(request, 'Account/profile.html', user_details)
        if not user.has_chat and user.can_be_matched:
            return redirect('results')
        if user.has_chat and user.can_be_matched:
            return redirect('chatroom')
        return redirect("dashboard")


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


# verified
def verified(request):
    print("Session: ", request.session)
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
        flash(request, 'Invalid Request !', 'danger', 'remove-sign')
        return redirect('login')

    if 'code' not in request.session:
        if 'verification_sent' in request.session:
            del request.session['verification_sent']
        flash(request, 'Code has expired !', 'danger', 'remove-sign')
        return redirect('login')

    del request.session['code']
    request.session['verified'] = True
    print(request.GET)
    request.session['email'] = purify_email(request.GET['email'])
    return redirect('verified')


# verified
def not_found(request):
    return render(request, 'Account/account-not-found.html')


# verified
def verification(request):
    if 'email' in request.session:
        return render(request, 'Account/verification-link-sent.html', {"email": request.session['email']})
    return redirect('login')


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

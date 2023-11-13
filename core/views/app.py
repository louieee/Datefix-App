from django.shortcuts import render, redirect
from django.contrib.auth.tokens import default_token_generator

from core.helpers.utilities import flash, display, purify_email
from core.models import User
from core.services.email_service import send_email


def home(request):
    if 'email' in request.session:
        del request.session['email']
    if 'category' in request.session:
        del request.session['category']
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        return render(request, 'home.html', {'user': user})
    return render(request, 'home.html')


def password_reset(request):
    if request.method == 'GET':
        alert = display(request)
        if alert is None:
            return render(request, 'registration/password_reset_form.html')
        else:
            return render(request, 'registration/password_reset_form.html', {"message": alert[0], "icon": alert[2],
                                                                             "status": alert[1]})

    if request.method == 'POST':
        email = request.POST['email']
        email = purify_email(email)
        try:
            user = User.objects.get(email=email)
            token_gen = default_token_generator
            secret = token_gen.secret
            token = token_gen.make_token(user)
            request.session['secret'] = secret
            request.session['email'] = email
            secret = secret.replace("&", "{}").replace("+", "[]").replace("%", "()")
            link_ = f'http://{request.get_host()}/confirm/?uidb64={secret}&token={token}'
            send_email(user.username, 'Password Reset',
                       f"You have requested to reset your password. To initiate the password reset process for your"
                       f" {user.username} Datefix Account, Follow the directions below.", user.email, link_,
                       None)
            return redirect('password_reset_done')
        except User.DoesNotExist:
            flash(request, 'This Email is Not Associated With Any Account.', 'danger', 'remove-sign')
            return redirect('password_reset')


def password_reset_done(request):
    email = request.session['email']
    return render(request, 'registration/password_reset_done.html', {"email": email})


def handler404_(request, exception):
    return render(request, '404.html', status=404)


def handler500_(request):
    return render(request, '404.html', status=500)


def handler403_(request, exception):
    return render(request, '404.html', status=403)


def password_confirm(request):
    uidb64 = request.GET['uidb64'].replace("{}", "&").replace('[]', '+').replace("()", "%")
    token = request.GET['token']
    d = default_token_generator
    if 'email' in request.session and 'secret' in request.session:
        user = User.objects.get(email=str(request.session['email']))
        if d.check_token(user, token) and uidb64 == str(request.session['secret']):
            return redirect('reset_confirm')
        else:
            flash(request, "This link is invalid !", "danger", "remove-sign")
            return redirect("password_reset")
    else:
        flash(request, "The link has expired !", "danger", "remove-sign")
        return redirect("password_reset")


def reset_confirm(request):
    if request.method == 'GET':
        return render(request, 'registration/password_reset_confirm.html')
    if request.method == 'POST':
        pass1 = request.POST.get('pass1', False)
        pass2 = request.POST.get('pass2', False)
        if not pass1 or not pass2:
            flash(request, 'Some form fields are empty', 'danger', 'remove-sign')
            return redirect('reset_confirm')
        if pass1 == pass2:
            user = User.objects.get(email=request.session['email'])
            user.set_password(pass1)
            user.save()
            del request.session['email'], request.session['secret']
            return redirect('password_reset_complete')
        else:
            flash(request, 'The passwords are not the same', 'danger', 'remove-sign')
            return redirect('reset_confirm')



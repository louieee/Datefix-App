from django.shortcuts import render, redirect

# Create your views here.
from django.shortcuts import render, redirect

# Create your views here.
from core.models import User, Couple


def chat(request):
	if request.user.is_authenticated:
		user = User.objects.get(id=request.user.id)
		if user.has_chat and user.can_be_matched:
			return render(request, 'Chat/chat.html')
		return redirect('dashboard')
	return redirect('home')


def session_end(request):
	user = User.objects.get(id=request.user.id)
	if request.method == 'GET':
		couple_list = user.couple_ids
		if len(couple_list) > 0:
			lists = (Couple.objects.get(id=x).true_details(user.id).items() for x in couple_list)
			return render(request, 'Chat/end_session.html', {"details": lists})
		return render(request, 'Chat/end_session.html')
	if request.method == 'POST':
		return redirect('dashboard')

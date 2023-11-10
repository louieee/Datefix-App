from django.shortcuts import render, redirect, HttpResponse

# Create your views here.
from Chat.utils import jilt
from Chat.models import ChatThread


def chat(request):
    if request.user.is_authenticated:
        from Account.models import User
        user = User.objects.get(id=request.user.id)
        if user.has_chat and user.can_be_matched:
            return render(request, 'Chat/chat.html')
        return redirect('dashboard')
    return redirect('home')


def get_chat_(request, id_):
    if request.method == 'GET':
        from Chat.utils import get_chat
        return HttpResponse(get_chat(id_, request.user))


def get_user(request, user_id):
    from Chat.utils import get_profile
    return HttpResponse(get_profile(request, user_id))


def user_chats(request):
    from Chat.utils import get_chat_threads
    return HttpResponse(get_chat_threads(request))


def delete_msg(request, chat_id, id_):
    from Chat.utils import delete_message
    return HttpResponse(delete_message(request, chat_id, id_))


def create_chat_api(request, user_id):
    from Chat.utils import create_chat
    import json
    return HttpResponse(json.dumps(create_chat(request, request.user.id, user_id)).replace("\\", ""))


def test_jilt(request, chat_id):
    try:
        chat = ChatThread.objects.get(id=chat_id)
        if chat.first_user_id == request.user.id or chat.second_user_id == request.user.id:
            from Account.models import User
            user = User.objects.get(id=request.user.id)
            jilt(chat, user, chat.get_receiver(user))
            return HttpResponse(
                f"Jilt was Successful. The Chat between {user.username} and {chat.get_receiver(user).username} has "
                f"been deleted")
        return HttpResponse("You are not in this chat")
    except ChatThread.DoesNotExist:
        return HttpResponse(f"The Chat with id {chat_id} has been deleted")


def test_accept(request, chat_id):
    from Chat.utils import select_match
    from Chat.models import ChatThread
    import json
    try:
        _chat = ChatThread.objects.get(id=chat_id)
        if _chat.first_user_id == request.user.id or _chat.second_user_id == request.user.id:
            from Account.models import User
            user = User.objects.get(id=request.user.id)
            data = select_match(_chat, _chat.get_receiver(user), user)
            return HttpResponse(json.dumps(data))
        return HttpResponse("You are not in this chat")
    except ChatThread.DoesNotExist:
        return HttpResponse(f"The Chat with id {chat_id} has been deleted")


def session_end(request):
    from Account.models import User
    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        couple_list = user.couple_ids
        if len(couple_list) > 0:
            from Account.models import Couple
            lists = (Couple.objects.get(id=x).true_details(user.id).items() for x in couple_list)
            return render(request, 'Chat/end_session.html', {"details": lists})
        return render(request, 'Chat/end_session.html')
    if request.method == 'POST':
        return redirect('dashboard')
import json

from django.db.models import Q
from django.shortcuts import redirect, HttpResponse
# Create your views here.
from core.models import ChatThread, User


def get_chat_(request, id_):
	if request.method == 'GET':
		return HttpResponse(ChatThread.get_chat(id_, request.user, as_json=True))

def user_chats(request):
	return HttpResponse(get_chat_threads(request))


def delete_msg(request, chat_id, id_):
	return HttpResponse(delete_message(request, chat_id, id_))


def create_chat_api(request, user_id):
	return HttpResponse(request.user.create_chat(second_user_id=user_id, as_json=True))


def test_jilt(request, chat_id):
	try:
		chat = ChatThread.objects.get(id=chat_id)
		if chat.first_user_id == request.user.id or chat.second_user_id == request.user.id:
			user = User.objects.get(id=request.user.id)
			chat.jilt(jilter=user)
			return HttpResponse(
				f"Jilt was Successful. The Chat between {user.username} and {chat.get_receiver(user).username} has "
				f"been deleted")
		return HttpResponse("You are not in this chat")
	except ChatThread.DoesNotExist:
		return HttpResponse(f"The Chat with id {chat_id} has been deleted")


def accept_chat_partner(request, chat_id):
	try:
		chat = ChatThread.objects.get(id=chat_id)
		if chat.first_user_id == request.user.id or chat.second_user_id == request.user.id:
			user = User.objects.get(id=request.user.id)
			data = chat.select_match(chat, first_user=user)
			return HttpResponse(json.dumps(data))
		return HttpResponse("You are not in this chat")
	except ChatThread.DoesNotExist:
		return HttpResponse(f"The Chat with id {chat_id} has been deleted")


def delete_message(request, chat_id, id_):
	"""
    This function deletes a message for only a particular user in a chat.
    :param request: HTTP request
    :param chat_id: chat instance id
    :param id_: chat message id
    :return:
    """
	chat = ChatThread.objects.get(id=chat_id)
	position = chat.position(request.user)
	deleted_msgs = {'first': chat.first_deleted, 'second': chat.second_deleted}
	deleted_msgs = deleted_msgs[position]
	deleted_msgs.append(id_)
	if position == 'first':
		chat.first_deleted = deleted_msgs
	elif position == 'second':
		chat.second_deleted = deleted_msgs
	chat.save()
	return id_

def get_chat_threads(request):
	"""
    This function returns all the chat instances that a logged in  user has.
    :param request: HTTP request
    :return: returns a JSON object containing the user's chats
    """
	user = User.objects.get(id=request.user.id)
	if request.method == 'GET':
		chats = ChatThread.objects.filter(Q(first_user_id=request.user.id) | Q(
			second_user_id=request.user.id)).order_by('-last_message_date')
		threads = [chat.serialized_data(user) for chat in chats]
		return json.dumps({'user_id': request.user.id,
		                   "chat_threads": threads})
	return redirect("not_found")

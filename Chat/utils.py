import json
from django.db.models import Q
from django.shortcuts import redirect
from django.utils import timezone
from datetime import datetime, timedelta
from Chat.models import ChatThread, ChatMessage


def select_match(chat_thread, user, you):
    from Account.models import Couple
    """
    This function enables a user to select another user to become a couple.
    :param chat_thread: The chat thread instance
    :param user: the user instance
    :param you: the other user instance
    :return: returns a response
    """
    position = chat_thread.position(user)
    if position == 'first':
        chat_thread.date_first = True
    elif position == "second":
        chat_thread.date_second = True
    chat_thread.save()

    if (position == 'first' and chat_thread.date_second) or (
            position == 'second' and chat_thread.date_first):
        couples = Couple.objects.filter(Q(first_partner_id=you.id, second_partner_id=user.id) |
                                        Q(first_partner_id=user.id, second_partner_id=you.id))
        if couples.count() == 0:
            couple = Couple.objects.create(first_partner_id=chat_thread.first_user_id,
                                           second_partner_id=chat_thread.second_user_id,
                                           datetime=datetime.now(), couple_name=chat_thread.chat_name())
            for i in [you, user]:
                couple_list = i.couple_ids
                if couple.id not in couple_list:
                    couple_list.append(couple.id)
                    i.couple_ids = couple_list
                    i.save()

        end_session(chat_thread, user, you)
        couple = Couple.objects.filter(Q(first_partner_id=you.id, second_partner_id=user.id) |
                                       Q(first_partner_id=user.id, second_partner_id=you.id))[0]
        return couple.id
    return f" You have accepted {user.username}. Awaiting Response from {user.username}"


def end_session(chat_thread, user, you):
    """
    This session ends a chat session between two users.
    :param chat_thread: the chat thread instance
    :param user: the user instance
    :param you: the other user instance
    :return:
    """
    for i in [user, you]:
        user_ = chat_thread.get_receiver(i)
        user_matches = i.matches
        try:
            user_matches.remove(int(user_.id))
            i.matches = user_matches
            if i.session == 2:
                i.session = 1
            elif i.session == 1:
                i.session = 0
            i.save()
        except ValueError:
            pass

    email_chat(chat_thread, user)
    email_chat(chat_thread, you)
    chat_thread.delete()
    return


def email_chat(chat_thread, user):
    """
    This function sends a message to a  user in a chat.
    :param chat_thread:  the chat instance
    :param user: the user instance
    :return:
    """
    other_user = chat_thread.get_receiver(user)
    user_chat = chat_thread.get_chat_file(user)
    message = f'This message indicates that the chat session between you and {other_user.username} ' \
              f'is formally over. Attached to this email address' \
              f'is a text file of the chat between you and {other_user.username}.'
    from Account.utils import send_email
    send_email(user.username, f'Chat Text File Between You and {user.username}.', message, user.email,
               None, [user_chat])
    import os
    os.remove(f"{user_chat['name']}")


def reject(you, user):
    jilted = you.jilted_matches
    if int(user.id) not in jilted:
        jilted.append(user.id)
        you.jilted_matches = jilted
        you.save()
    return


def jilt(chat, you, user):
    """
    This function ends a chat session between two users
    :param chat: the user instance
    :param you: a user instance
    :param user: the other user instance
    :return:
    """
    reject(you, user)
    reject(user, you)
    end_session(chat, user, you)
    return


def get_chat(chat_id, user):
    """
    This function returns the chat message for a particular user in a chat.
    :param chat_id: chat instance id
    :param user: user instance
    :return: a JSON object containing the chat message
    """
    chat_thread = ChatThread.objects.get(id=chat_id)
    return json.dumps(chat_thread.get_chat(chat_thread.position(user)))


def get_chat_threads(request):
    from Account.models import User, Couple
    """
    This function returns all the chat instances that a logged in  user has.
    :param request: HTTP request
    :return: returns a JSON object containing the user's chats
    """
    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        chats = ChatThread.objects.filter(Q(first_user_id=request.user.id) | Q(
            second_user_id=request.user.id)).order_by('-last_message_date')
        data = tuple([chat.serialized_data(user) for chat in chats])
        return json.dumps({'user_id': request.user.id, "chat_threads": data})


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


def profile_picture(image):
    """
    This function checks if an image exists and returns None or the image.
    :param image: The image url
    :return:
    """
    try:
        return image.url
    except ValueError:
        return None


def get_profile(request, user_id):
    from Account.models import User
    """
    This function returns the user details of a user and all the chat threads that belong to that user.
    :param request: HTTP request
    :param user_id: user id
    :return:
    """
    if request.method == 'GET':
        user = User.objects.get(id=user_id)
        return json.dumps({'username': user.username,
                           'first_name': user.first_name, 'last_name': user.last_name,
                           'profile_pic': profile_picture(user.profile_picture),
                           'status': user.status,
                           'threads': user.chatThreads()})
    return redirect("not_found")


def create_chat(request, your_id: int, user_id: int):
    from Account.models import User
    """
    This function creates a chat session between two users.
    :param request: HTTP request
    :param your_id: The first user instance
    :param user_id: The  second user instance
    :return:
    """
    if request.user.id == user_id:
        return 'You Cannot Chat With Yourself.'
    chats = ChatThread.objects.filter(Q(first_user_id=your_id, second_user_id=user_id) |
                                      Q(first_user_id=user_id, second_user_id=your_id))
    if chats.count() > 0:
        return 'This Chat Thread Object Already Exists'
    else:
        from Datefix.algorithms import get_key
        user = User.objects.get(id=user_id)
        user_matches = user.matches
        user_matches.append(your_id)
        user.matches = user_matches
        user.save()
        secret = get_key(f'{your_id}{datetime.now().timestamp()}{user_id}')
        expiry_date = timezone.now() + timedelta(days=30)
        chat = ChatThread.objects.create(first_user_id=your_id,
                                         second_user_id=user_id,
                                         secret=secret, expiry_date=expiry_date)
        return {"status": 200, "message": f'A Chat Thread Object has been created for you and the '
                                          f'user with ID {user_id}',
                "data": get_chat(chat.id, user=request.user)}


def activate_expiration(chat, user):
    """
    This function sets an expiration date for a chat session the moment.
    :param chat: the chat thread instance
    :param user: the user instance
    :return:
    """
    your_msgs = ChatMessage.objects.filter(chat_id=chat.id, sender_id=user.id)
    receiver = chat.get_receiver(user)
    their_msgs = ChatMessage.objects.filter(chat_id=chat.id, sender_id=receiver.id)
    if their_msgs.count() > 0 and your_msgs.count() == 0:
        chat.expiry_date = timezone.now() + timedelta(days=7)
        chat.save()
        if user.session == -1:
            user.session = 1
        else:
            user.session = 2
        user.save()
        if receiver.session == -1:
            receiver.session = 1
        else:
            receiver.session = 2
        receiver.save()
        chat.notify_user(user=user, new_match=False)
        chat.notify_user(user=receiver, new_match=False)


def purify_email(email:str):
    email = email.lower()
    email = email.replace(' ', '')
    return email

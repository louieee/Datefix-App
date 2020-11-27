import base64

from django.db import models
from Account.models import User
from django.conf import settings
from datetime import timedelta, timezone
from django.utils.datetime_safe import datetime


# Create your models here.


class ChatThread(models.Model):
    first_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='chatter1')
    second_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='chatter2')
    show_first = models.BooleanField(default=True)
    show_second = models.BooleanField(default=True)
    date_created = models.DateTimeField()
    date_first = models.NullBooleanField(default=None, blank=True, null=True)
    date_second = models.NullBooleanField(default=None, blank=True, null=True)
    show_details = models.BooleanField(default=False)
    first_deleted = models.TextField(default='[]')
    second_deleted = models.TextField(default='[]')
    secret = models.BinaryField()
    expiry_date = models.DateTimeField(default=None)
    last_message_date = models.DateTimeField(default=None, null=True)

    def chat_name(self):
        return f'User_{self.first_user_id} and User_{self.second_user_id}'

    def self_delete(self):
        if not self.show_first and not self.show_second:
            self.delete()

        if self.date_first is False or self.date_second is False:
            self.delete()

    def show_detail(self):
        if self.date_created == (self.date_created + (timedelta(days=7))):
            self.show_details = True

    def first_deleted_(self):
        return str(self.first_deleted).split(',')

    def expired(self):
        if self.expiry_date.__lt__(datetime.now().astimezone()):
            return True
        return False

    def second_deleted_(self):
        return str(self.second_deleted).split(',')

    def chat_messages(self, user_position):
        list_ = {'first': self.first_deleted_(), 'second': self.second_deleted_()}
        chat_message_items = [x for x in ChatMessage.objects.all().filter(chat_id=self.id).order_by('datetime') \
                              if x.id not in list_[user_position]]
        decrypted_messages = [self.decrypt(x.text) for x in chat_message_items]
        return zip(chat_message_items, decrypted_messages)

    def get_chat_file(self, user):
        user_position = self.position(user)
        other_user = self.get_receiver(user)
        list_ = {'first': self.first_deleted_(), 'second': self.second_deleted_()}
        chat_message_items = [x for x in ChatMessage.objects.all().filter(chat_id=self.id).order_by('datetime') \
                              if x.id not in list_[user_position]]
        decrypted_messages = [self.decrypt(x.text) for x in chat_message_items]
        text_file = open(f'Chat_with_{other_user.username}.txt', 'w+')
        text_file.write(f'Chat Between {user.username} and {other_user.username}.\n\n')
        for item, msg in zip(chat_message_items, decrypted_messages):
            text_file.write(f"{item.sender.username} "
                            f"({item.datetime.time().strftime('%I:%M %p')}): {msg}\n")

        text_file.close()
        return {
            "content": base64.b64encode(text_file.read().encode()).decode(),
            "type": "text/plain",
            "filename": f'Chat_with_{other_user.username}.txt'
        }

    def get_chat(self, user_position):
        list_ = {'first': self.first_deleted_(), 'second': self.second_deleted_()}
        self.self_delete()
        self.show_detail()
        chat_message_items = [x for x in ChatMessage.objects.all().filter(chat_id=self.id).order_by('datetime') \
                              if x.id not in list_[user_position]]

        from Chat.algorithms import profile_picture
        data = tuple([{'id': i.id,
                         'time': i.datetime.strftime('%I:%M %p'),
                         'date': i.datetime.strftime('%e - %b - %Y'),
                         'message': self.decrypt(i.text),
                         'sender_id': i.sender.id,
                         'sender': i.sender.username,
                         'sender_pic': profile_picture(i.sender.profile_picture),
                         'status': i.send_status} for i in chat_message_items])
        status = ''
        if user_position == 'first':
            status = User.objects.get(id=self.second_user_id).status

        if user_position == 'second':
            status = User.objects.get(id=self.first_user_id).status
        data = {'chat_id': self.id, 'expired': self.expired(), 'status': status, 'chat_list': data}
        return data

    def get_receiver(self, user):
        if self.first_user_id == user.id:
            return User.objects.get(id=self.second_user_id)
        else:
            return User.objects.get(id=self.first_user_id)

    def position(self, user):
        if self.first_user_id == user.id:
            return 'first'
        return 'second'

    def last_message(self):
        msg = ChatMessage.objects.filter(chat=self).order_by('-datetime')
        if msg.count() == 0:
            return None
        return msg[0]

    def last_message_text(self):
        try:
            return self.decrypt(self.last_message().text)
        except AttributeError:
            return None

    def encrypt(self, data):
        from cryptography.fernet import Fernet
        return Fernet(self.secret).encrypt(data.encode()).decode()

    def decrypt(self, cipher_text):
        from cryptography.fernet import Fernet
        return Fernet(self.secret).decrypt(cipher_text.encode()).decode()

    def no_unread_msg(self, user):
        receiver = self.get_receiver(user)
        position = self.position(user)
        list_ = {'first': self.first_deleted_(), 'second': self.second_deleted_()}
        chat_message_items = tuple([x for x in ChatMessage.objects.filter(chat=self) \
            .filter(sender=receiver).filter(send_status='sent').order_by('datetime') \
                              if x.id not in list_[position]])
        return len(chat_message_items)

    def first_msg_today(self):
        chat_msg = ChatMessage.objects.filter(chat=self).filter(datetime=datetime.today()).order_by('id')
        return chat_msg[0]


class ChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    text = models.TextField()
    datetime = models.DateTimeField()
    send_status = models.CharField(max_length=20, choices=(('sent', 'sent'), ('delivered', 'delivered')))
    chat = models.ForeignKey(ChatThread, on_delete=models.CASCADE)

    def expired(self):
        if (datetime.now(timezone.utc) - self.datetime) > timedelta(seconds=180):
            return True
        return False

import base64
import json
from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.datetime_safe import datetime

from core.models import User
from core.services.email_service import send_email


# Create your models here.


class ChatThread(models.Model):
	first_user = models.ForeignKey("core.User", on_delete=models.DO_NOTHING, related_name='chatter1')
	second_user = models.ForeignKey("core.User", on_delete=models.DO_NOTHING, related_name='chatter2')
	show_first = models.BooleanField(default=True)
	show_second = models.BooleanField(default=True)
	date_created = models.DateTimeField(auto_now_add=True)
	date_first = models.BooleanField(default=None, blank=True, null=True)
	date_second = models.BooleanField(default=None, blank=True, null=True)
	show_details = models.BooleanField(default=False)
	first_deleted = models.JSONField(default=list, blank=True)
	second_deleted = models.JSONField(default=list, blank=True)
	secret = models.BinaryField()
	expiry_date = models.DateTimeField(default=None, blank=True, null=True)
	last_message_date = models.DateTimeField(default=None, null=True, blank=True)

	def notify_user(self, user, new_match=True):
		other_user = self.get_receiver(user)
		message = 'This message indicates that the chat session between the two of you has formally began.'
		send_email(user.username, f'Chat Session Between You and {other_user.username}.', message,
		           user.email, None, None)
		if new_match:
			message = f'{self.get_receiver(user).username} has been matched to you.'
			send_email(user.username, 'New Match', message,
			           user.email, None, None)
		return

	def activate_expiration(self, user):
		"""
		This function sets an expiration date for a chat session the moment.
		:param chat: the chat thread instance
		:param user: the user instance
		:return:
		"""
		your_msgs = ChatMessage.objects.filter(chat_id=self.id, sender_id=user.id)
		receiver = self.get_receiver(user)
		their_msgs = ChatMessage.objects.filter(chat_id=self.id, sender_id=receiver.id)
		if their_msgs.count() > 0 and your_msgs.count() == 0:
			self.expiry_date = timezone.now() + timedelta(days=7)
			self.save()
			receiver.save()
			self.notify_user(user=user, new_match=False)
			self.notify_user(user=receiver, new_match=False)

	def serialized_data(self, user):
		return {
			"chat_id": self.id,
			"chat_link": ''.join(['/chat/api/chat/', str(self.id)]),
			"username": self.get_receiver(user).username,
			"status": self.get_receiver(user).status,
			"first_name": self.get_receiver(user).first_name,
			"last_name": self.get_receiver(user).last_name,
			"profile_picture": self.get_receiver(user).get_profile_picture,
			"last_message": self.last_message.serialized_data if self.last_message else None,
			"expired": self.expired
		}

	def chat_name(self):
		return f'User_{self.first_user_id} and User_{self.second_user_id}'

	def self_delete(self):
		if not self.show_first and not self.show_second:
			self.delete()

		if not self.date_first or not self.date_second:
			self.delete()

	def show_detail(self):
		if (timezone.now() - self.date_created).days == 7:
			self.show_details = True
			self.save()
		return

	@property
	def expired(self):
		if not self.expiry_date:
			return False
		return self.expiry_date.__lt__(timezone.now())

	def chat_messages(self, user_position):
		list_ = {'first': self.first_deleted,
		         'second': self.second_deleted}
		return ChatMessage.objects.all().filter(Q(~Q(id__in=list_[user_position]),
		                                          chat_id=self.id)).order_by('datetime')

	def get_chat_file(self, user):
		user_position = self.position(user)
		other_user = self.get_receiver(user)
		chat_messages = self.chat_messages(user_position)
		text_file = open(f'Chat_with_{other_user.username}.txt', 'w+')
		text_file.write(f'Chat Between {user.username} and {other_user.username}.\n\n')
		for msg in chat_messages:
			text_file.write(f"{msg.sender.username} "
			                f"({msg.datetime.time().strftime('%I:%M %p')}): {msg.actual_text}\n")
		content = base64.b64encode(text_file.read().encode()).decode()
		text_file.close()
		return {
			"content": content,
			"type": "text/plain",
			"filename": f'Chat_with_{other_user.username}.txt'
		}

	def get_chat(self, user_position, as_json=False):
		chat_message_items = self.chat_messages(user_position)

		data = tuple([msg.serialized_data for msg in chat_message_items])
		status = ''
		if user_position == 'first':
			status = User.objects.get(id=self.second_user_id).status
		if user_position == 'second':
			status = User.objects.get(id=self.first_user_id).status
		data = {'chat_id': self.id, 'expired': self.expired, 'status': status, 'chat_list': data}
		if as_json:
			return json.dumps(data)
		return data

	def get_receiver(self, user):
		if self.first_user_id == user.id:
			return User.objects.get(id=self.second_user_id)
		else:
			return User.objects.get(id=self.first_user_id)

	def position(self, user):
		return "first" if self.first_user_id == user.id else "second"

	@property
	def last_message(self):
		return ChatMessage.objects.filter(chat=self).order_by('-datetime').first()

	def last_message_text(self):
		if self.last_message:
			return self.last_message.actual_text
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
		list_ = {'first': self.first_deleted, 'second': self.second_deleted}
		return ChatMessage.objects.filter(chat=self, sender=receiver, send_status='sent') \
			.filter(~Q(id__in=list_[position])).count()

	def first_msg_today(self):
		return ChatMessage.objects.filter(chat=self). \
			filter(datetime=timezone.now().today()).order_by('id').first()

	@staticmethod
	def reject(you, user):
		jilted = you.jilted_matches
		if int(user.id) not in jilted:
			jilted.append(user.id)
			you.jilted_matches = jilted
			you.save()
		return

	def jilt(self, jilter):
		"""
	    This function ends a chat session between two users
	    :param chat: the user instance
	    :param jilter: a user instance
	    :param jiltee: the other user instance
	    :return:
	    """
		jiltee = self.get_receiver(jilter)
		self.reject(jilter, jiltee)
		self.reject(jiltee, jilter)
		self.end_session(jiltee, jilter)
		return

	def email_chat(self, user):
		"""
	    This function sends a message to a  user in a chat.
	    :param chat_thread:  the chat instance
	    :param user: the user instance
	    :return:
	    """
		other_user = self.get_receiver(user)
		user_chat = self.get_chat_file(user)
		message = f'This message indicates that the chat session between you and {other_user.username} ' \
		          f'is formally over. Attached to this email address' \
		          f'is a text file of the chat between you and {other_user.username}.'
		send_email(user.username, f'Chat Text File Between You and {user.username}.', message, [user.email],
		           None, [user_chat])
		import os
		os.remove(f"{user_chat['filename']}")

	def end_session(self, user, you):
		"""
	    This session ends a chat session between two users.
	    :param chat_thread: the chat thread instance
	    :param user: the user instance
	    :param you: the other user instance
	    :return:
	    """
		for i in [user, you]:
			second_user = self.get_receiver(i)
			user_matches = i.matches
			if second_user.id in user_matches:
				user_matches.remove(int(second_user.id))
			i.matches = user_matches
			i.save()
			self.email_chat(i)
		self.delete()
		return

	def select_match(self, first_user):
		from core.models import Couple
		"""
	    This function enables a user to select another user to become a couple.
	    :param chat_thread: The chat thread instance
	    :param user: the user instance
	    :param you: the other user instance
	    :return: returns a response
	    """
		second_user = self.get_receiver(first_user)
		position = self.position(second_user)
		if position == 'first':
			self.date_first = True
		elif position == "second":
			self.date_second = True
		self.save()

		if (position == 'first' and self.date_second) or (
				position == 'second' and self.date_first):
			couples = Couple.objects.filter(Q(first_partner_id=first_user.id, second_partner_id=second_user.id) |
			                                Q(first_partner_id=second_user.id, second_partner_id=first_user.id))
			if couples.count() == 0:
				couple = Couple.objects.create(first_partner_id=self.first_user_id,
				                               second_partner_id=self.second_user_id,
				                               datetime=datetime.now(), couple_name=self.chat_name())
				for i in [first_user, second_user]:
					couple_list = i.couple_ids
					if couple.id not in couple_list:
						couple_list.append(couple.id)
						i.couple_ids = couple_list
						i.save()

			self.end_session(second_user, first_user)
			couple = Couple.objects.filter(Q(first_partner_id=first_user.id, second_partner_id=second_user.id) |
			                               Q(first_partner_id=second_user.id, second_partner_id=first_user.id))[0]
			return couple.id
		return f" You have accepted {second_user.username}. Awaiting Response from {second_user.username}"


class ChatMessage(models.Model):
	sender = models.ForeignKey("core.User", on_delete=models.DO_NOTHING)
	text = models.TextField()
	datetime = models.DateTimeField()
	send_status = models.CharField(max_length=20, choices=(('sent', 'sent'), ('delivered', 'delivered')))
	chat = models.ForeignKey(ChatThread, on_delete=models.CASCADE)

	@property
	def expired(self):
		return (timezone.now() - self.datetime).total_seconds() > 180

	@property
	def actual_text(self):
		return self.chat.decrypt(self.text)

	@property
	def serialized_data(self):
		return {'id': self.id,
		        'time': self.datetime.strftime('%I:%M %p'),
		        'date': self.datetime.strftime('%e - %b - %Y'),
		        'message': self.actual_text,
		        'sender_id': self.sender.id,
		        'sender': self.sender.username,
		        'sender_pic': self.sender.profile_pic,
		        'status': self.send_status}

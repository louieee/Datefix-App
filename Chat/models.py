from django.db import models
from django.db.models import Q
from django.utils import timezone
from Account.models import User


# Create your models here.


class ChatThread(models.Model):
	first_user = models.ForeignKey("Account.User", on_delete=models.DO_NOTHING, related_name='chatter1')
	second_user = models.ForeignKey("Account.User", on_delete=models.DO_NOTHING, related_name='chatter2')
	show_first = models.BooleanField(default=True)
	show_second = models.BooleanField(default=True)
	date_created = models.DateTimeField()
	date_first = models.BooleanField(default=None, blank=True, null=True)
	date_second = models.BooleanField(default=None, blank=True, null=True)
	show_details = models.BooleanField(default=False)
	first_deleted = models.JSONField(default=list)
	second_deleted = models.JSONField(default=list)
	secret = models.BinaryField()
	expiry_date = models.DateTimeField(default=None)
	last_message_date = models.DateTimeField(default=None, null=True)

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

	def expired(self):
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
		text_file.close()
		return text_file

	def get_chat(self, user_position):
		self.self_delete()
		self.show_detail()
		chat_message_items = self.chat_messages(user_position)

		data = tuple([msg.serialized_data for msg in chat_message_items])
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


class ChatMessage(models.Model):
	sender = models.ForeignKey("Account.User", on_delete=models.DO_NOTHING)
	text = models.TextField()
	datetime = models.DateTimeField()
	send_status = models.CharField(max_length=20, choices=(('sent', 'sent'), ('delivered', 'delivered')))
	chat = models.ForeignKey(ChatThread, on_delete=models.CASCADE)

	def expired(self):
		return (timezone.now() - self.datetime).total_seconds() > 180

	@property
	def actual_text(self):
		return self.chat.decrypt(self.text)

	@property
	def serialized_data(self):
		from Chat.algorithms import profile_picture
		return {'id': self.id,
		        'time': self.datetime.strftime('%I:%M %p'),
		        'date': self.datetime.strftime('%e - %b - %Y'),
		        'message': self.actual_text,
		        'sender_id': self.sender.id,
		        'sender': self.sender.username,
		        'sender_pic': profile_picture(self.sender.profile_picture),
		        'status': self.send_status}

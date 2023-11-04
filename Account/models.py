from django.db import models
import os
from django.core.validators import validate_email
from django.contrib.auth.models import AbstractUser
import json
from django.db.models import Q


class User(AbstractUser):
	sex = models.CharField(max_length=6, default=None, null=True)
	phone = models.CharField(max_length=16, default=None, null=True)
	user_data = models.JSONField(default=dict)
	choice_data = models.JSONField(default=dict)
	deal_breaker = models.JSONField(default=list)
	profile_picture = models.ImageField(upload_to='profile_pics', blank=True)
	matches = models.JSONField(default=list)
	successful_matches = models.JSONField(default=list)
	no_matches = models.JSONField(default=list)
	jilted_matches = models.JSONField(default=list)
	couple_ids = models.JSONField(default=list)
	session = models.IntegerField(default=-1)
	verified = models.BooleanField(default=False)
	status = models.CharField(max_length=64, default='Offline')
	can_be_matched = models.BooleanField(default=False)
	extra_support = models.BooleanField(default=False)
    email = models.EmailField(unique=True, validators=[validate_email])

	@property
	def complete_match(self):
		return self.matches.__len__() >= 2

	@property
	def is_couple(self):
		return Couple.objects.filter(Q(first_partner=self) | Q(second_partner=self)).exists()

	@property
	def origin(self):
		return self.user_data.get('origin_state', '')

	@property
	def residence(self):
		return f"{self.user_data.get('residence_address', '')} {self.user_data.get('residence_state', '')}"

	@property
	def religion(self):
		return self.user_data.get('religion', '')

	@property
	def denomination(self):
		return self.user_data.get('denomination', '')

	@property
	def has_children(self):
		return self.user_data.get('children', '')

	def personality(self):
		test = PersonalityTest.objects.filter(email=self.email).first()
		return test.titles() if test else list()

	@property
	def chats(self):
		from Chat.models import ChatThread
		return ChatThread.objects.filter(Q(first_user_id=self.id) | Q(second_user_id=self.id)).values_list("id",
		                                                                                                   flat=True)


class Couple(models.Model):
	first_partner = models.ForeignKey("Account.User", on_delete=models.DO_NOTHING, related_name='match1')
	second_partner = models.ForeignKey("Account.User", on_delete=models.DO_NOTHING, related_name='match2')
	couple_name = models.CharField(max_length=30, default='')
	datetime = models.DateTimeField()

	def true_details(self, user_id):
		if self.first_partner_id == user_id:
			user = User.objects.filter(id=self.second_partner_id).first()
		elif self.second_partner_id == user_id:
			user = User.objects.filter(id=self.first_partner_id).first()
		else:
			return None
		if user is None:
			return None
		return {"firstName": user.first_name,
		        "lastName": user.last_name, "phone": user.phone, "email": user.email,
		        "residential_address": user.residence,
		        "origin_address": f"{user.user_data.get('origin_lga', '')}, {user.origin}"}


class PersonalityTest(models.Model):
	email = models.EmailField()
	extraversion = models.JSONField(default=dict)
	neurotism = models.JSONField(default=dict)
	agreeableness = models.JSONField(default=dict)
	conscientiousness = models.JSONField(default=dict)
	openness = models.JSONField(default=dict)

	def titles(self):
		real = lambda x: json.loads(x)['title'] if 'title' in json.loads(x) else ''
		return tuple([real(self.extraversion), real(self.neurotism),
		              real(self.agreeableness), real(self.conscientiousness),
		              real(self.openness)])

from datetime import timedelta

from django.db import models
import os
from django.core.validators import validate_email
from django.contrib.auth.models import AbstractUser
import json
from django.db.models import Q
from django.utils import timezone

from core.helpers.utilities import _2_point, _3_point


class User(AbstractUser):
	sex = models.CharField(max_length=6, default=None, null=True)
	phone = models.CharField(max_length=16, default=None, null=True)
	user_data = models.JSONField(default=dict, blank=True)
	choice_data = models.JSONField(default=dict, blank=True)
	deal_breaker = models.JSONField(default=list, blank=True)
	profile_picture = models.ImageField(upload_to='profile_pics', blank=True)
	matches = models.JSONField(default=list, blank=True)
	successful_matches = models.JSONField(default=list, blank=True)
	no_matches = models.JSONField(default=list, blank=True)
	jilted_matches = models.JSONField(default=list, blank=True)
	couple_ids = models.JSONField(default=list, blank=True)
	verified = models.BooleanField(default=False)
	status = models.CharField(max_length=64, default='Offline')
	can_be_matched = models.BooleanField(default=False)
	extra_support = models.BooleanField(default=False)
	email = models.EmailField(unique=True, validators=[validate_email])

	def update_matchability(self):
		from core.models import Payment # noqa
		payment = Payment.objects.filter(Q(payer_id=self.id) & Q(status='PAID')).last()
		if not payment:
			return False
		if payment.expiry_date.__lt__(timezone.now()):
			payment.delete()
			self.can_be_matched = False
			self.extra_support = False
			self.save()
			return False
		return True

	@property
	def complete_match(self):
		return self.matches.__len__() >= 1

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
		from core.models import ChatThread # noqa
		return ChatThread.objects.filter(Q(first_user_id=self.id) | Q(second_user_id=self.id)).values_list("id",
		                                                                                                   flat=True)

	@property
	def has_chat(self):
		from core.models import ChatThread # noqa
		return ChatThread.objects.filter(Q(first_user=self)|Q(second_user=self)).exists()

	@property
	def profile_pic(self):
		return self.profile_picture.url if self.profile_picture else None

	def match_user(self):
		"""
	    This function matches a particular user to other users based on the compatibility scores.
	    :param self:  The user instance.
	    :return:  it is a void.
	    """
		success_list = {}
		no_list = []
		# filter users
		gender = "male" if str(self.sex).lower() == "female" else "female"
		all_users = User.objects.filter(Q(~Q(id__in=self.jilted_matches)
		                                  & ~Q(id__in=self.no_matches) &
		                                  ~Q(user_data=dict())),
		                                sex__iexact=gender, can_be_matched=True).only('id')
		all_users = (user for user in all_users if not user.complete_match and not user.is_couple)
		# compare filtered users with user and return matches

		for second_user in all_users:
			peep_score = self.compare_users(second_user)
			my_score = second_user.compare_users(self)
			try:
				if peep_score >= 50 and my_score >= 50:
					success_list[second_user.id] = peep_score
				else:
					no_list.append(str(second_user.id))
			except KeyError:
				no_list.append(str(second_user.id))
		success_list = sorted(success_list.items(), key=lambda x: x[1], reverse=True)
		self.successful_matches = success_list
		self.no_matches = no_list
		self.save()

	def compare_users(self, another_user):
		"""
	    This function compares two users against each other to determine their compatibility.
	    :param self: first user.
	    :param another_user: second user.
	    :return: it returns the percentage of their compatibility.
	    """
		mark = 0
		absolute_match = ('residence_lga', 'residence_state', 'origin_lga',
		                  'origin_state', 'denomination', 'religion', 'marital_status', 'children',
		                  'blood_group', 'genotype')

		_2_spectrum = ('net_worth', 'education', 'body_shape')

		_3_spectrum = ('complexion', 'height', 'body_type', 'drink', 'smoke', 'conscientiousness', 'openess',
		               'extraversion', 'agreeableness', 'neurotism')
		deal_breakers = self.deal_breaker
		total = len(absolute_match) + len(_3_spectrum) + len(_2_spectrum) + 1

		for i in deal_breakers:
			if i == 'No Dealbreaker':
				continue
			try:
				if str(self.choice_data[i]) == str(another_user.user_data[i]):
					mark += 1
				else:
					return 0
			except KeyError:
				continue

		for i in absolute_match:
			try:
				if str(another_user.user_data[i]) in str(self.choice_data[i]) \
						or 'Does Not Matter' == str(self.choice_data[i]):
					mark = mark + 1
			except KeyError:
				continue

		for i in _2_spectrum:
			try:
				if str(self.choice_data[i]) == 'Does Not Matter':
					mark = mark + 1
				else:
					mark = mark + _2_point(self.choice_data[i], 5, another_user.user_data[i])
			except KeyError:
				continue

		for i in _3_spectrum:
			try:
				mark = mark + _3_point(self.choice_data[i], another_user.user_data[i])
			except KeyError:
				continue
		try:
			mark = mark + self.age_range(another_user)
		except KeyError:
			pass
		return (mark / total) * 100

	def age_range(self, other_user):
		"""
	    This function checks if a particular age falls into a specified range or close to the range.
	    :param self: the person who specified the range.
	    :param other_user: the person who has the age.
	    :return: returns a point assigned to the age.
	    """
		min_age = self.choice_data['min-age']
		max_age = self.choice_data['max-age']
		age = other_user.user_data['age']
		if int(age) in range(int(min_age), int(max_age)):
			return 1
		# grace of 4 years for each range
		elif abs(int(min_age) - int(age)) < 5 and abs(int(max_age) - int(age)) < 5:
			return 0.5
		else:
			return 0

	def create_chat(self, second_user_id: int, as_json=False):
		from Datefix.utils import get_key
		from core.models import ChatThread
		if self.id == second_user_id:
			return 'You Cannot Chat With Yourself.'
		if ChatThread.objects.filter(Q(first_user_id=self.id, second_user_id=second_user_id) |
		                             Q(first_user_id=second_user_id, second_user_id=self.id)).exists():
			return 'This Chat Thread Object Already Exists'
		success = self.successful_matches
		success = [x for x in success if x[0] != second_user_id]
		self.successful_matches = success
		self.save()
		user = User.objects.get(id=second_user_id)
		user_matches = user.matches
		user_matches.append(self.id)
		user.matches = user_matches
		user.save()
		secret = get_key(f'{self.id}{timezone.now().timestamp()}{second_user_id}')
		expiry_date = timezone.now() + timedelta(days=30)
		chat = ChatThread.objects.create(first_user_id=self.id,
		                                 second_user_id=second_user_id,
		                                 secret=secret, expiry_date=expiry_date)
		if as_json:
			return chat.serialized_data(self)
		return chat

	@property
	def serialized_data(self):
		return {'username': self.username,
		 'first_name': self.first_name, 'last_name': self.last_name,
		 'profile_pic': self.profile_pic,
		 'status': self.status,
		 'threads': list(self.chats)}


class Couple(models.Model):
	first_partner = models.ForeignKey("core.User", on_delete=models.DO_NOTHING, related_name='match1')
	second_partner = models.ForeignKey("core.User", on_delete=models.DO_NOTHING, related_name='match2')
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

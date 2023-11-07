import logging

from django.utils.datetime_safe import datetime
from decouple import config
import requests
from Payment.models import Payment


class RavePayServices:
	def __init__(self, data):
		self.data = data
		self.link = None

	@staticmethod
	def package_price(package, duration):
		if package == 'REGULAR' and duration == 'QUARTERLY':
			return 1500
		if package == 'PREMIUM' and duration == 'QUARTERLY':
			return 6000
		if package == 'REGULAR' and duration == 'YEARLY':
			return 5500
		if package == 'PREMIUM' and duration == 'YEARLY':
			return 20000

	@staticmethod
	def get_user(user_id):
		from Account.models import User
		return User.objects.get(id=user_id)

	def create_payment_model(self):
		user = self.get_user(self.data['data']['customer']['id'])
		Payment.objects.create(user=user, status='PAID', tx_ref=self.data['data']['tx_ref'],
							   date_of_payment=datetime.now(), package=self.data['data']['customer']['package'])

	def make_payment(self):
		user = self.get_user(self.data['user_id'])
		url = f"{config('RAVE_PAY_BASE_URL')}/payments"
		headers = {"Authorization": f"Bearer {config('RAVE_PAY_KEY')}"}
		tx_ref = self.create_tx_ref()
		data = {"tx_ref": tx_ref, "amount": self.package_price(self.data['package'], self.data['duration']),
				"currency": "NGN",
				"redirect_url": f"{config('RAVE_PAY_REDIRECT_URL')}/{user.id}/{self.data['package']}/{self.data['duration']}/{tx_ref}",
				"payment_options": "account, card, banktransfer, ussd",
				"customer": {
					"id": user.id, "email": user.email, "name": f"{user.first_name} {user.last_name}",
					"package": self.data['package'],
					"duration": self.data['duration']
				}, "customizations": {
				"title": "DateFix Payments",
				"description": f"Payment for the {self.data['package']} package",
				"logo": config('LOGO_URL')
			}}
		try:
			result = requests.post(url=url, headers=headers, json=data).json()
			if result['status'] == 'success':
				self.link = result['data']['link']
				return True
			return False
		except Exception as e:
			#TODO will change it back to False
			logging.critical(f"RAVE ERROR: {e}")
			return True

	def create_tx_ref(self):
		import secrets
		tx_ref = secrets.token_hex(16)
		try:
			Payment.objects.get(tx_ref__exact=tx_ref)
			self.create_tx_ref()
		except Payment.DoesNotExist:
			return tx_ref

from django.db.models import Q


def can_be_matched(user_id):
	from Account.models import User
	from Payment.models import Payment
	from datetime import datetime
	user = User.objects.get(id=user_id)
	payment = Payment.objects.filter(Q(payer_id=user.id) & Q(status='PAID')).last()
	if payment is None:
		return False
	if payment.expiry_date < datetime.now().astimezone():
		payment.delete()
		user.can_be_matched = False
		user.extra_support = False
		user.save()
		return False
	return True


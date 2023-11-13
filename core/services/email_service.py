from threading import Thread
from typing import List

from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_mail_thread(**kwargs):
	if "attachments" in kwargs:
		EmailMessage(**kwargs).send(fail_silently=True)
		return
	send_mail(**kwargs)
	return


def send_email(user, title: str, message: str, to: List[str] | str, link=None, attachments=None):
	if isinstance(to, str):
		to = [to]
	if link is not None:
		html_message = render_to_string('Account/mailer.html',
		                                {"link": link, "message": message, "subject": title, "user": user})
	else:
		html_message = render_to_string('Account/mailer.html',
		                                {"message": message, "subject": title, "user": user})
	plain_message = strip_tags(html_message)
	from_email = 'admin@datefix.net'

	if attachments is None:
		data = dict(subject=title, message=plain_message, from_email=from_email,
		            recipient_list=to, fail_silently=False)
	else:
		data = dict(subject=title, body=plain_message, from_email=from_email,
		            to=to, attachments=attachments)

	thread = Thread(target=send_mail_thread, kwargs=data)
	thread.start()
	return

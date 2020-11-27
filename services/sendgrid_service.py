import requests
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from decouple import config

BASE_URL = "https://api.sendgrid.com/v3"

API_KEY = config('SENDGRID_API_KEY')
HEADER = {"Authorization": f'Bearer {API_KEY}', "Content-Type": "application/json"}


def authorize():
	response = requests.get(url=f'{BASE_URL}/templates', headers=HEADER)
	return response.json()


def promotion_mail(user, title, message, to=None, link=None, attachments=None):
	if to is None:
		to = []
	if link is not None:
		html_message = render_to_string('Account/mailer.html',
										{"link": link, "message": message, "subject": title, "user": user})
	else:
		html_message = render_to_string('Account/mailer.html',
										{"message": message, "subject": title, "user": user})
	plain_message = strip_tags(html_message)
	url = f'{BASE_URL}/mail/send'
	json = {
		"personalizations": [{
			"to": to
		}],
		"from": {
			"email": "admin@datefix.net",
			"name": "DateFix Team"
		},
		"subject": title,
		"content": [
			{
				"type": "text/plain",
				"value": plain_message
			},
			{
				"type": "text/html",
				"value": html_message
			}
		],
	}
	if attachments is not None:
		json['attachments'] = attachments
	response = requests.post(url=url, json=json, headers=HEADER)
	return response


def direct_mail(user, title, message, to, link, attachments=None):
	from django.core.mail import EmailMultiAlternatives
	from django.template.loader import render_to_string
	from django.utils.html import strip_tags
	if link is not None:
		html_message = render_to_string('Account/mailer.html',
										{"link": link, "message": message, "subject": title, "user": user})
	else:
		html_message = render_to_string('Account/mailer.html',
										{"message": message, "subject": title, "user": user})
	plain_message = strip_tags(html_message)
	from_email = 'admin@datefix.com'
	message = EmailMultiAlternatives(title, plain_message, from_email, [to])
	message.attach_alternative(html_message, 'text/html')
	if attachments is not None:
		for i in attachments:
			message.attach_file(i)
	message.send(True)


def send_email(user, title, message, to, link=None, attachments=None, promotion=None):
	if promotion:
		promotion_mail(user, title, message, to, link, attachments)
	else:
		direct_mail(user, title, message, to, link, attachments)

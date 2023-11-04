
import os

import requests
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from decouple import config

BASE_URL_PRO = "https://api.sendgrid.com/v3"
BASE_URL_DIR = "https://api.sendgrid.com/api/mail.send.json"

API_KEY = config('SENDGRID_API_KEY')
HEADER = {"Authorization": f'Bearer {API_KEY}', "Content-Type": "application/json"}


def authorize():
	response = requests.get(url=f'{BASE_URL_PRO}/templates', headers=HEADER)
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
	url = f'{BASE_URL_PRO}/mail/send'
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


def direct_mail(user, title, message, to, link=None, attachments=None):
	if link is not None:
		html_message = render_to_string('Account/mailer.html',
										{"link": link, "message": message, "subject": title, "user": user})
	else:
		html_message = render_to_string('Account/mailer.html',
										{"message": message, "subject": title, "user": user})
	plain_message = strip_tags(html_message)
	url = f'{BASE_URL_PRO}/mail/send'
	json = {
		"personalizations": [{
			--------"to": [{"email": to}]
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

def stmp_mail(user, title, message, to, link=None, attachments=None):
	if link is not None:
		html_message = render_to_string('Account/mailer.html',
										{"link": link, "message": message, "subject": title, "user": user})
	else:
		html_message = render_to_string('Account/mailer.html',
										{"message": message, "subject": title, "user": user})
	plain_message = strip_tags(html_message)
	# The email body for recipients with non-HTML email clients.
	body_text = plain_message
	# The HTML body of the email.
	body_html = html_message
	charset = "utf-8"
	import boto3
	client = boto3.client('ses', region_name='us-east-2')
	from email.mime.multipart import MIMEMultipart
	msg = MIMEMultipart('mixed')
	# Add subject, from and to lines.
	msg['Subject'] = title
	msg['From'] = 'admin@datefix.net'
	msg['To'] = to
	msg_body = MIMEMultipart('alternative')
	from email.mime.text import MIMEText
	textpart = MIMEText(body_text.encode(charset), 'plain', charset)
	htmlpart = MIMEText(body_html.encode(charset), 'html', charset)
	# Add the text and HTML parts to the child container.
	msg_body.attach(textpart)
	msg_body.attach(htmlpart)
	# Define the attachment part and encode it using MIMEApplication.
	msg.attach(msg_body)

	if attachments is not None:
		from email.mime.application import MIMEApplication
		for i in attachments:
			att = MIMEApplication(open(i['filename'], 'rb').read())
			att.add_header('Content-Disposition', 'attachment', filename=i['filename'])
			if os.path.exists(i['filename']):
				print("File exists")
			else:
				print("File does not exists")
			# Attach the multipart/alternative child container to the multipart/mixed
			# parent container.
			# Add the attachment to the parent container.
			msg.attach(att)

	from botocore.exceptions import ClientError
	try:
		# Provide the contents of the email.
		response = client.send_raw_email(
			Source=msg['From'],
			Destinations=[
				msg['To']
			],
			RawMessage={
				'Data': msg.as_string(),
			}
		)
	# Display an error if something goes wrong.
	except ClientError as e:
		return e.response['Error']['Message']
	else:
		return "Email sent! Message ID:", response['MessageId']


def send_email(user, title, message, to, link=None, attachments=None, promotion=None):
	if promotion:
		promotion_mail(user, title, message, to, link, attachments)
	else:
		stmp_mail(user, title, message, to, link, attachments)



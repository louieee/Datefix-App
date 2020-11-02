from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from decouple import config


def send_email(user, title, message, to, link=None, attachments=None):
	sg = SendGridAPIClient(config('SENDGRID_API_KEY'))

	if link is not None:
		html_message = render_to_string('Account/mailer.html',
										{"link": link, "message": message, "subject": title, "user": user})
	else:
		html_message = render_to_string('Account/mailer.html',
										{"message": message, "subject": title, "user": user})
	plain_message = strip_tags(html_message)
	from_email = 'admin@datefix.com'

	message = Mail(
		from_email=from_email,
		to_emails=to,
		subject=title,
		plain_text_content=plain_message,
		html_content=html_message)
	if attachments is not None:
		for i in attachments:
			message.add_attachment(i)
	response = sg.send(message)
	return response


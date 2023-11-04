from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_email(user, title, message, to, link=None, attachments=None):
    if link is not None:
        html_message = render_to_string('Account/mailer.html',
                                        {"link": link, "message": message, "subject": title, "user": user})
    else:
        html_message = render_to_string('Account/mailer.html',
                                        {"message": message, "subject": title, "user": user})
    plain_message = strip_tags(html_message)
    from_email = 'admin@datefix.net'
    send_mail(subject=title, message=plain_message, from_email=from_email,
              recipient_list=to, html_message=html_message, fail_silently=False)
    if attachments is None:
        attachments = list()
    
    EmailMessage(subject=title, body=html_message, from_email=from_email,
                                     to=to, attachments=attachments).send(fail_silently=False)
    return




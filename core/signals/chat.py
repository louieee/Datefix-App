from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import ChatThread


@receiver(post_save, sender=ChatThread)
def notify_chat_users(sender, instance, created, **kwargs):
	if instance:
		instance.notify(instance.first_user)
		instance.notify(instance.second_user)

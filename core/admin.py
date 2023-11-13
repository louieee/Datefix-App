# Register your models here.
from django.contrib import admin

from .models import ChatMessage, ChatThread, Payment, User, Couple, PersonalityTest

admin.site.register(ChatMessage)
admin.site.register(ChatThread)

# Register your models here.


# Register your models here.

admin.site.register(User)
admin.site.register(Couple)
admin.site.register(PersonalityTest)

admin.site.register(Payment)

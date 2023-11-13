from django.urls import path

from core.views import chat

urlpatterns = [
    path('', chat.chat, name='chatroom'),
    path('end_session/', chat.session_end, name="end_session"),
  ]

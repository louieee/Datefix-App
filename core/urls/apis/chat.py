from django.urls import path
from core.apis import chat

urlpatterns = [
	path('<int:id_>/', chat.get_chat_, name="get_chat_api"),
	path('/', chat.user_chats, name="get_threads_api"),
	path('create/<user_id>/', chat.create_chat_api, name="create_chat"),
	path('<chat_id>/message/<id_>/delete/', chat.delete_msg, name="del_4_you"),
	path('jilt/<int:chat_id>/', chat.test_jilt, name="jilt"),
	path('accept/<int:chat_id>/', chat.accept_chat_partner, name="accept")
]

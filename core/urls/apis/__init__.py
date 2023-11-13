from django.urls import path, include

urlpatterns = [
    path('accounts/', include('core.urls.apis.account')),
    path('chats/', include('core.urls.apis.chat'))
]
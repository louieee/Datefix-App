"""Datefix URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500, handler403
from django.conf import settings
from .views import home, handler404_, handler403_, handler500_

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Account.urls')),
    path('chat/', include('Chat.urls')),
    path('payment/', include('Payment.urls')),
    path('', home, name='home'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = handler404_

handler500 = handler500_

handler403 = handler403_

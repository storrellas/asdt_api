"""asdt_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path(settings.PREFIX + '/admin/', admin.site.urls),
    path(settings.PREFIX + '/user/', include('user.urls')),
    path(settings.PREFIX + '/groups/', include('groups.urls')),
    path(settings.PREFIX + '/logs/', include('logs.urls')),
    path(settings.PREFIX + '/drones/', include('drones.urls')),
    path(settings.PREFIX + '/detectors/', include('detectors.urls')),
    path(settings.PREFIX + '/inhibitors/', include('inhibitors.urls')),
    path(settings.PREFIX + '/zones/', include('zones.urls')),
]
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

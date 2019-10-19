# Django imports
from django.conf.urls import url, include


# Project imports
from .views import *

urlpatterns = [
    url(r'^info/$', UserInfo.as_view()),
    url(r'^me/allowedTools$', AllowedTools.as_view()),
    url(r'^me/displayOptions$', DisplayOptions.as_view()),
]



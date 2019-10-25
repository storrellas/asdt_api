# Django imports
from django.conf.urls import url, include
from django.urls import path


# Project imports
from .views import *

# urlpatterns = [
#     url(r'^info/$', UserInfo.as_view()),
#     url(r'^me/allowedTools$', AllowedTools.as_view()),
#     url(r'^me/displayOptions$', DisplayOptions.as_view()),
# ]

urlpatterns = [
    path('authenticate/', Authenticate.as_view()),
    path('info/', UserInfo.as_view()),
    path('tools/', Tools.as_view())
]



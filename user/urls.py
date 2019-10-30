# Django imports
from django.conf.urls import url, include
from django.urls import path


# Project imports
from .views import *

urlpatterns = [
    path('authenticate/', UserAuthenticateView.as_view()),
    path('me/', UserMeView.as_view()),
    path('me/tools/', UserToolsView.as_view()),
    path('', UserView.as_view())
]



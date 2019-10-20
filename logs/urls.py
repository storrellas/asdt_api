# Django imports
from django.conf.urls import url, include


# Project imports
from .views import *

urlpatterns = [
    url(r'^getAll$', GetFlightAll.as_view()),
    url(r'^single$', GetFlightByPage.as_view()),
    url(r'^$', GetFlightByPage.as_view()),
]


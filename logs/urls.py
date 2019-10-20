# Django imports
from django.conf.urls import url
from django.urls import path, include


# Project imports
from .views import *

urlpatterns = [
    url(r'^getAll$', GetFlightAll.as_view()),
    path('<str:log_id>', LogById.as_view()),
    url(r'^$', LogByPage.as_view()) 
    
]


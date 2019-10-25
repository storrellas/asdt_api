# Django imports
from django.conf.urls import url
from django.urls import path, include


# Project imports
from .views import *

urlpatterns = [    
    path('<str:log_id>/', LogByIdView.as_view()),
    url(r'^$', LogByPageView.as_view()) 
]


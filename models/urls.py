# Django imports
from django.conf.urls import url
from django.urls import path, include


# Project imports
from .views import *

urlpatterns = [    
    path('<str:model_id>/img', ModelImg.as_view()),
    url(r'^$', Model.as_view()) 
]


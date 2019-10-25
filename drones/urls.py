# Django imports
from django.conf.urls import url
from django.urls import path, include


# Project imports
from .views import *

urlpatterns = [    
    path('<str:model_id>/img', DroneModelImgView.as_view()),
    url(r'^$', DroneModelView.as_view()) 
]


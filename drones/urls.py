# Django imports
from django.conf.urls import url
from django.urls import path, include


# Project imports
from .views import *

urlpatterns = [    
    #path('model/<str:model_id>/img', DroneModelImgView.as_view()),
    path('model/', DroneModelView.as_view()) 
]


# Django imports
from django.conf.urls import url
from django.urls import path, include


# DRF inludes
from rest_framework import routers

# Project imports
from .views import *

# Project imports
from .views import *

# Do not change the order as URL resolution is done in order
router = routers.DefaultRouter()
router.register(r'', DroneViewset, basename='user')

urlpatterns = [    
    #path('model/<str:model_id>/img', DroneModelImgView.as_view()),
    path('model/', DroneModelView.as_view()),
    path('', include(router.urls))
]


# Django imports
from django.conf.urls import url, include
from django.urls import path

# DRF inludes
from rest_framework import routers

# Project imports
from .views_devices import *
from .views import *

# Do not change the order as URL resolution is done in order
router = routers.DefaultRouter()
router.register(r'', GroupViewset, basename='user')
router.register(r'(?P<group_id>[a-zA-Z0-9]+)/devices/detectors', GroupDetectorViewset, basename='user')
router.register(r'(?P<group_id>[a-zA-Z0-9]+)/devices/drones', GroupDroneViewset, basename='user')
router.register(r'(?P<group_id>[a-zA-Z0-9]+)/devices/inhibitors', GroupInhibitorViewset, basename='user')
router.register(r'(?P<group_id>[a-zA-Z0-9]+)/devices/zones', GroupZoneViewset, basename='user')

urlpatterns = [
    path('all/', GroupAllView.as_view()),
    path('<str:group_id>/users/<str:user_id>/', GroupUserView.as_view()),
    path('', include(router.urls))
]



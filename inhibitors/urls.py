# Django imports
from django.conf.urls import url, include
from django.urls import path

# DRF inludes
from rest_framework import routers

# Project imports
from .views import *

# Do not change the order as URL resolution is done in order
router = routers.DefaultRouter()
router.register(r'', InhibitorViewset, basename='user')

urlpatterns = [
    path('', include(router.urls))
]



# Django imports
from django.conf.urls import url
from django.urls import path, include

# DRF inludes
from rest_framework import routers

# Project imports
from .views import *

# Do not change the order as URL resolution is done in order
router = routers.DefaultRouter()
router.register(r'', LogViewSet, basename='log')

# urlpatterns = [    
#     path('', include(router.urls)),  
# ]

urlpatterns = router.urls


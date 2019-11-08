# Django imports
from django.conf.urls import url, include
from django.urls import path

# DRF inludes
from rest_framework import routers

# Project imports
from .views import *

# # Do not change the order as URL resolution is done in order
# router = routers.DefaultRouter()
# router.register(r'', InhibitorView, basename='Inhibitor')

# urlpatterns = [
#     #path('me/', UserMeView.as_view()),
#     #path('me/tools/', UserToolsView.as_view()),
#     path('', include(router.urls))
# ]



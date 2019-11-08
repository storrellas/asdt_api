# Django imports
from django.conf.urls import url, include
from django.urls import path

# DRF inludes
from rest_framework import routers

# Project imports
from .views import *
from .views_crud import *

# Do not change the order as URL resolution is done in order
router = routers.DefaultRouter()
router.register(r'', GroupView, basename='user')

urlpatterns = [
    path('all/', GroupAllView.as_view()),
    path('<str:group_id>/users/<str:user_id>/', GroupUserView.as_view()),
    path('<str:group_id>/devices/inhibitors/<str:inhibitor_id>/', GroupInhibitorView.as_view()),
    path('<str:group_id>/devices/detectors/<str:detector_id>/', GroupDetectorView.as_view()),
    #path('me/', UserMeView.as_view()),
    #path('me/tools/', UserToolsView.as_view()),
    path('', include(router.urls))
]



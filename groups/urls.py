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

urlpatterns = [
    path('all/', GroupAllView.as_view()),
    path('<str:group_id>/users/<str:user_id>/', GroupUserView.as_view()),
    # path('<str:group_id>/devices/detectors/<str:instance_id>/', GroupDetectorView.as_view()),
    # path('<str:group_id>/devices/drones/<str:instance_id>/', GroupDroneView.as_view()),
    # path('<str:group_id>/devices/inhibitors/<str:instance_id>/', GroupInhibitorView.as_view()),
    # path('<str:group_id>/devices/zones/<str:instance_id>/', GroupZoneView.as_view()),
    #path('me/', UserMeView.as_view()),
    #path('me/tools/', UserToolsView.as_view()),
    path('', include(router.urls))
]



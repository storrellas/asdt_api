# Django imports
from django.conf.urls import url
from django.urls import path, include


# Project imports
from .views import *

urlpatterns = [    
    path('<str:model_id>/img', ModelDetectorImgView.as_view()),
    url(r'^$', ModelDetectorView.as_view()) 
]


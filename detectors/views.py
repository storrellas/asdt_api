from django.shortcuts import render

from django.conf import settings

# rest framework import
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.decorators import action, permission_classes

# Project imports
from asdt_api.utils import get_logger
from asdt_api.authentication import ASDTIsAdminOrMasterPermission, ASDTAuthentication
from asdt_api.models import Location
from asdt_api.views import DeviceViewset


from .models import *
from groups.models import *

logger = get_logger()

class LocationDetectorSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    height = serializers.FloatField()

class DetectorSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    password = serializers.CharField(max_length=72, required=False)
    location = LocationDetectorSerializer(required=False)

class DetectorViewset(DeviceViewset):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, ASDTIsAdminOrMasterPermission, )

    model = Detector
    serializer = DetectorSerializer

    def get_id_list_allowed(self, request):
      """
      Returns all ids allowed for current user
      """
      id_list = []
      for item in self.devices.detectors:
        id_list.append(str(item.fetch().id) )
      return id_list

    def get_groups(self, instance):
      """
      Returns all groups associated to instance
      """
      return Group.objects.filter(devices__detectors__in=[instance.id])

    # def list(self, request):
    #   """
    #   Retrieve all inhibitors 
    #   """
    #   return super().list(request)

    # def retrieve(self, request, pk=None):
    #   """
    #   Retrieve single inhibitors 
    #   """
    #   return super().retrieve(request, pk)

    # def create(self, request):
    #   """
    #   Retrieve all inhibitors 
    #   """
    #   return super().update(request)

    # def update(self, request, pk=None):
    #   """
    #   Update inhibitors 
    #   """
    #   return super().update(request, pk)

    # def delete(self, request, pk=None):
    #   """
    #   Delete inhibitors 
    #   """
    #   return super().update(request, pk)

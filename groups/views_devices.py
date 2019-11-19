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

# Project imports
from asdt_api.utils import get_logger
from asdt_api.authentication import ASDTIsAdminOrMasterPermission, ASDTAuthentication
from asdt_api.models import Location

from .models import *
from inhibitors.models import Inhibitor
from zones.models import Zone
from detectors.models import Detector
from drones.models import Drone

logger = get_logger()


class GroupDevicesViewset(viewsets.ViewSet):

    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, ASDTIsAdminOrMasterPermission)
    model = None
    queryset = None
    group = None

    def list(self, request, *args, **kwargs):
      try:
        self.group = Group.objects.get(id=kwargs['group_id'])
        if request.user.is_allowed_group(self.group) == False:
          raise APIException("NOT_ALLOWED")
        
        # Generate data
        data = []
        for instance in self.get_devicelist():
          data.append(instance.fetch().as_dict())
        # TODO: No necessary to return anything just a 204
        #data = func(group)

        return Response(data)
      except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, *args, **kwargs):
      try:

        # Retrieve models
        group = Group.objects.get(id=kwargs['group_id'])
        instance = self.model.objects.get(id=kwargs['pk'])
        if request.user.is_allowed_group(group) == False:
          raise APIException("NOT_ALLOWED")

        # Add device to group        
        instance.groups.append(group)
        instance.save()
        group.append_device(instance)
        group.save()

        return Response( instance.as_dict() )
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
      

    def delete(self, request, *args, **kwargs):
      try:

        # Retrieve models
        group = Group.objects.get(id=kwargs['group_id'])
        instance = self.model.objects.get(id=kwargs['pk'])
        if request.user.is_allowed_group(group) == False:
          raise APIException("NOT_ALLOWED")

        # Add inhibitor to group        
        instance.groups.remove(group)
        instance.save()
        group.remove_device(instance)
        group.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GroupDetectorViewset(GroupDevicesViewset):

    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, ASDTIsAdminOrMasterPermission, )
    model = Detector
    group = None

    def get_devicelist(self):
      return self.group.devices.detectors

class GroupDroneViewset(GroupDevicesViewset):

    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, ASDTIsAdminOrMasterPermission, )
    model = Drone
    group = None

    def get_devicelist(self):
      return self.group.devices.friendDrones

class GroupInhibitorViewset(GroupDevicesViewset):

    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, ASDTIsAdminOrMasterPermission, )
    model = Inhibitor
    group = None

    def get_devicelist(self):
      return self.group.devices.inhibitors

class GroupZoneViewset(GroupDevicesViewset):

    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, ASDTIsAdminOrMasterPermission, )
    model = Zone
    group = None

    def get_devicelist(self):
      return self.group.devices.zones

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
from asdt_api.authentication import *
from asdt_api.models import Location

from .models import *
from inhibitors.models import Inhibitor
from zones.models import Zone
from detectors.models import Detector
from drones.models import Drone

logger = get_logger()


class GroupDevicesView(APIView):

    def post(self, request, *args, **kwargs):
      try:
        # TODO: Put all this logic into a function
        if request.user.role != 'ADMIN':
          raise APIException("NOT_ALLOWED")

        # Retrieve models
        group = Group.objects.get(id=kwargs['group_id'])
        instance = self.model.objects.get(id=kwargs['instance_id'])
        if request.user.is_allowed_group(group) == False:
          raise APIException("NOT_ALLOWED")

        # Add device to group        
        instance.groups.append(group)
        instance.save()
        group.append_device(instance)
        group.save()

        return Response({"success": True, "data": str(instance.id)})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})
      

    def delete(self, request, *args, **kwargs):
      try:
        # TODO: Put all this logic into a function
        if request.user.role != 'ADMIN':
          raise APIException("NOT_ALLOWED")

        # Retrieve models
        group = Group.objects.get(id=kwargs['group_id'])
        instance = self.model.objects.get(id=kwargs['instance_id'])
        if request.user.is_allowed_group(group) == False:
          raise APIException("NOT_ALLOWED")

        # Add inhibitor to group        
        instance.groups.remove(group)
        instance.save()
        group.remove_device(instance)
        group.save()

        return Response({"success": True, "data": str(instance.id)})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})

class GroupDetectorView(GroupDevicesView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)
    model = Detector

class GroupDroneView(GroupDevicesView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)
    model = Drone

class GroupInhibitorView(GroupDevicesView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, )
    model = Inhibitor

class GroupZoneView(GroupDevicesView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)
    model = Zone


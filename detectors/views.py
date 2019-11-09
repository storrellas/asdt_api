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
from asdt_api.authentication import *
from asdt_api.models import Location
from asdt_api.views import DeviceViewset

from .models import *
from groups.models import *

logger = get_logger()

class DetectorViewset(DeviceViewset):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    model = Detector

    def get_id_list_allowed(self, request):
      """
      Returns all ids allowed for current user
      """
      id_list = []
      for item in self.devices.detectors:
        id_list.append(str(item.fetch().id) )
      return id_list

    def create(self, request):
      return Response({"success": True, "data": "create"})

    def list(self, request):
      """
      Retrieve all inhibitors 
      """
      return super().list(request)

    def retrieve(self, request, pk=None):
      return Response({"success": True, "data": "retrieve"})
      # try:
      #   # Get ids
      #   self.devices = request.user.group.get_full_devices()

      #   # Get queryset
      #   id_list = self.get_queryset(request)

      #   # check if allowed
      #   if pk not in id_list:
      #     raise APIException('NOT_ALLOWED')

      #   # Generate queryset
      #   item = self.model.objects.filter(id__in=id_list)
      #   device_dict = []
      #   for item in queryset:
      #     device_dict.append(item.as_dict())

      #   return Response({'success': True, 'data': device_dict})
      # except Exception as e:
      #   print(e)
      #   return Response({"success": False, "error": str(e)})

    def update(self, request, pk=None):
      return Response({"success": True, "data": "update"})

    def delete(self, request, pk=None):
      return Response({"success": True, "data": "delete"})

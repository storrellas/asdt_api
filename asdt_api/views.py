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
from .utils import get_logger
from .authentication import *
from .models import Location

from groups.models import *

logger = get_logger()

class DeviceViewset(viewsets.ViewSet):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    model = None
    devices = None

    def get_id_list_allowed(self, request):
      """
      Returns all ids allowed for current user
      """
      return []

    def list(self, request):
      """
      Retrieve all inhibitors 
      """
      try:
        # Get ids
        self.devices = request.user.group.get_full_devices()

        # Get queryset
        id_list = self.get_id_list_allowed(request)
        
        # Generate queryset
        queryset = self.model.objects.filter(id__in=id_list)
        device_dict = []
        for item in queryset:
          device_dict.append(item.as_dict())

        return Response({'success': True, 'data': device_dict})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})

    def retrieve(self, request, pk=None):
      #return Response({"success": True, "data": "retrieve"})
      try:
        # Get ids
        self.devices = request.user.group.get_full_devices()

        # Get queryset
        id_list = self.get_id_list_allowed(request)

        # check if allowed
        if pk not in id_list:
          raise APIException('NOT_ALLOWED')

        # Generate queryset
        item = self.model.objects.get(id=pk)

        return Response({'success': True, 'data': item.as_dict() })
      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})


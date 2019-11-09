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

    def get_queryset(self, request):
      pass

    def list(self, request):
      """
      Retrieve all inhibitors 
      """
      try:
        # Get ids
        self.devices = request.user.group.get_full_devices()

        # Get queryset
        id_list = self.get_queryset(request)
        
        # Generate queryset
        queryset = self.model.objects.filter(id__in=id_list)
        device_dict = []
        for item in queryset:
          device_dict.append(item.as_dict())

        return Response({'success': True, 'data': device_dict})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})


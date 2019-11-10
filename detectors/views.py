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

class LocationUserSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    height = serializers.FloatField()

class DetectorSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    password = serializers.CharField(max_length=72)
    location = LocationUserSerializer()
    #groups = serializers.ListField(child=serializers.CharField())


class DetectorViewset(DeviceViewset):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

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

    def create(self, request):
      try:
        if request.user.role != 'ADMIN':
          raise APIException("NOT_ALLOWED")

        # Validate Serializer
        serializer = DetectorSerializer(data=request.data)
        if serializer.is_valid() == False:
          print({'message': serializer.errors})
          raise APIException(serializer.errors)

        # Create object
        data = serializer.validated_data
        instance = self.model.objects.create(**data)

        # Check whether groups exist and apply them to model
        if 'groups' in request.data:
          
          # Adding to groups
          for group_id in request.data['groups']:
            # Add device to group
            group = Group.objects.get(id=group_id)
            group.append_device(instance)

            # Add group to device
            instance.groups.append(group)
          
          # Save instance
          instance.save()

        return Response({'success': True, 'data': instance.as_dict() })
      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})

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

    def update(self, request, pk=None):
      try:
        if request.user.role != 'ADMIN':
          raise APIException("NOT_ALLOWED")

        # Validate Serializer
        serializer = DetectorSerializer(data=request.data)
        if serializer.is_valid() == False:
          print({'message': serializer.errors})
          raise APIException(serializer.errors)

        # Update object        
        data = serializer.validated_data
        instance = self.model.objects.get(id=pk)
        instance.update(**data)
        
        # Check whether groups exist and apply them to model        
        if 'groups' in request.data:
          # Remove device from groups
          for group in instance.groups:
            group.remove_device(instance)

          # Adding to groups
          instance.groups = []
          for group_id in request.data['groups']:
            
            # Add device to group
            group = Group.objects.get(id=group_id)
            group.append_device(instance)

            # Add group to device
            instance.groups.append(group)
          
          instance.save()

        # Get updated object
        instance = self.model.objects.get(id=pk)
        return Response({'success': True, 'data': instance.as_dict() })
      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})


    def delete(self, request, pk=None):
      try:
        if request.user.role != 'ADMIN':
          raise APIException("NOT_ALLOWED")

        # Update object        
        instance = self.model.objects.get(id=pk)

        # Remove item from groups
        for group in instance.groups:
          group.remove_device(instance)

        # Delete instance        
        instance.delete()
        return Response({'success': True, 'data': '' })
      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})

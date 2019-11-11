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
      Retrieve all models 
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

        return Response(device_dict)
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
      """
      Retrieve single model
      """
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

        return Response(item.as_dict())
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
      """
      Create model
      """
      try:
        if request.user.role != 'ADMIN':
          raise APIException("NOT_ALLOWED")

        # Validate Serializer
        serializer = self.serializer(data=request.data)
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

        return Response(instance.as_dict())
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
      """
      Update model
      """
      try:
        if request.user.role != 'ADMIN':
          raise APIException("NOT_ALLOWED")

        # Validate Serializer
        serializer = self.serializer(data=request.data)
        if serializer.is_valid() == False:
          print({'message': serializer.errors})
          raise APIException(serializer.errors)

        # Update object        
        data = serializer.validated_data

        # Check if parameter to update
        instance = self.model.objects.get(id=pk)
        if len(data) > 0:
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
        return Response(instance.as_dict())
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk=None):
      """
      Delete model
      """
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
        return Response(status=status.HTTP_204_NO_CONTENT)
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
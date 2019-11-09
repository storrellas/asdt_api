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
from logs.models import Detector, Zone
from drones.models import Drone

logger = get_logger()


class GroupUserView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
      """
      Adds user to group
      """
      try:
        # TODO: Put all this logic into a function
        if request.user.role != 'ADMIN':
          raise APIException("NOT_ALLOWED")
        
        # Get instances
        group = Group.objects.get(id=kwargs['group_id'])
        user = User.objects.get(id=kwargs['user_id'])

        # Check whether request user has id
        if request.user.group is None:
          raise APIException("GROUP_ID_NOT_FOUND")

        # Check permissions
        if request.user.group.is_parent_of( group ):
          pass
        elif request.user.group == group and user.role == 'ADMIN':
          # If targeted user is ADMIN do not allow to modify group
          raise APIException("NOT_ALLOWED")
        else:
          raise APIException("NOT_ALLOWED")

        # Remove user from current group
        if user.group is not None:
          user.group.users.remove(user)
          user.group.save()

        # Set group to user
        user.group = group
        user.save()

        # Add user to group
        group.users.append(user)
        group.save()
        

        return Response({"success": True, "data": str(user.id)})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})


    def delete(self, request, *args, **kwargs):
      """
      Removes user from group
      """
      try:
        if request.user.role != 'ADMIN':
          raise APIException("NOT_ALLOWED")


        # Get instances
        group = Group.objects.get(id=kwargs['group_id'])
        user = User.objects.get(id=kwargs['user_id'])
        # Check whether request user has id
        if request.user.group is None:
          raise APIException("GROUP_ID_NOT_FOUND")

        # Check permissions
        if request.user.group.is_parent_of( group ):
          pass
        elif request.user.group == group and user.role == 'ADMIN':
          # If targeted user is ADMIN do not allow to modify group
          raise APIException("NOT_ALLOWED")
        else:
          raise APIException("NOT_ALLOWED")

        # Remove user from group
        if user.group is not None:
          user.group.users.remove(user)
          user.group.save()

        user.group = None
        user.save()

        return Response({"success": True, "data": str(user.id)})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})


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

class GroupInhibitorView(GroupDevicesView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, )
    
    model = Inhibitor
    
    def post(self, request, *args, **kwargs):
      """
      Adds inhibitor to group
      """
      return super().post(request, *args, **kwargs)


    def delete(self, request, *args, **kwargs):
      """
      Removes inhibitor from group
      """
      return super().delete(request, *args, **kwargs)



class GroupDetectorView(GroupDevicesView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    model = Detector
    
    def post(self, request, *args, **kwargs):
      """
      Adds inhibitor to group
      """
      return super().post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
      """
      Removes inhibitor from group
      """
      return super().delete(request, *args, **kwargs)


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

# Project imports
from asdt_api.utils import get_logger
from asdt_api.authentication import *
from asdt_api.models import Location

from .models import *
#from .serializers import *

logger = get_logger()


class GroupUserView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
      """
      Adds user to group
      """
      # TODO: Put all this logic into a function
      if request.user.role != 'ADMIN':
        return Response({"success": False, "data": "NOT_ALLOWED"})
      # Get paramters
      group_id = kwargs['group_id']
      user_id = kwargs['user_id']

      try:
        group = Group.objects.get(id=group_id)
        user = User.objects.get(id=user_id)
        # Check whether request user has id
        if request.user.group is None:
          return Response({"success": False, "error": "GROUP_ID_NOT_FOUND"})

        # Check permissions
        if request.user.group.is_parent_of( group ):
          pass
        elif request.user.group == group and user.role == 'ADMIN':
          # If targeted user is ADMIN do not allow to modify group
          return Response({"success": False, "data": "NOT_ALLOWED"})
        else:
          return Response({"success": False, "data": "NOT_ALLOWED"})

        # Remove user from current group
        if user.group is not None:
          user.group.remove_user(user)
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
        return Response({"success": False, "error": "DOES_NOT_EXIST"})


    def delete(self, request, *args, **kwargs):
      """
      Removes user from group
      """
      if request.user.role != 'ADMIN':
        return Response({"success": False, "data": "NOT_ALLOWED"})
      # Get paramters
      group_id = kwargs['group_id']
      user_id = kwargs['user_id']

      try:
        group = Group.objects.get(id=group_id)
        user = User.objects.get(id=user_id)
        # Check whether request user has id
        if request.user.group is None:
          return Response({"success": False, "error": "GROUP_ID_NOT_FOUND"})

        # Check permissions
        if request.user.group.is_parent_of( group ):
          pass
        elif request.user.group == group and user.role == 'ADMIN':
          # If targeted user is ADMIN do not allow to modify group
          return Response({"success": False, "data": "NOT_ALLOWED"})
        else:
          return Response({"success": False, "data": "NOT_ALLOWED"})

        # Remove user from group
        user.group.remove_user(user)
        user.group.save()

        user.group = None
        user.save()

        return Response({"success": True, "data": str(user.id)})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": "DOES_NOT_EXIST"})
      return Response({"success": False, "data": "NOT_ALLOWED"})

class GroupInhibitorView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
      """
      Adds inhibitor to group
      """
      # TODO: Put all this logic into a function
      if request.user.role != 'ADMIN':
        return Response({"success": False, "data": "NOT_ALLOWED"})
      # Get paramters
      group_id = kwargs['group_id']
      inhibitor_id = kwargs['inhibitor_id']
      
      # try:
      #   group = Group.objects.get(id=group_id)
      #   inhibitor = Inhibitor.objects.get(id=inhibitor_id)
      #   # Check whether request user has id
      #   if request.user.group is None:
      #     return Response({"success": False, "error": "GROUP_ID_NOT_FOUND"})

      #   # Check permissions
      #   if request.user.group.is_parent_of( group ):
      #     pass
      #   elif request.user.group == group and user.role == 'ADMIN':
      #     # If targeted user is ADMIN do not allow to modify group
      #     return Response({"success": False, "data": "NOT_ALLOWED"})
      #   else:
      #     return Response({"success": False, "data": "NOT_ALLOWED"})

      #   # Remove user from group
      #   user.group.remove_user(user)
      #   user.group.save()

      #   user.group = None
      #   user.save()

      #   return Response({"success": True, "data": str(user.id)})
      # except Exception as e:
      #   print(e)
      #   return Response({"success": False, "error": "DOES_NOT_EXIST"})
      # return Response({"success": False, "data": "NOT_ALLOWED"})


      return Response({"success": True, "error": ""})


    def delete(self, request, *args, **kwargs):
      """
      Removes inhibitor to group
      """
      # TODO: Put all this logic into a function
      if request.user.role != 'ADMIN':
        return Response({"success": False, "data": "NOT_ALLOWED"})
      # Get paramters
      group_id = kwargs['group_id']
      user_id = kwargs['inhibitor_id']

      return Response({"success": True, "error": ""})


class GroupDetectorView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
      """
      Adds inhibitor to group
      """
      # TODO: Put all this logic into a function
      if request.user.role != 'ADMIN':
        return Response({"success": False, "data": "NOT_ALLOWED"})
      # Get paramters
      group_id = kwargs['group_id']
      user_id = kwargs['detector_id']

      return Response({"success": True, "error": ""})


    def delete(self, request, *args, **kwargs):
      """
      Removes inhibitor to group
      """
            # TODO: Put all this logic into a function
      if request.user.role != 'ADMIN':
        return Response({"success": False, "data": "NOT_ALLOWED"})
      # Get paramters
      group_id = kwargs['group_id']
      user_id = kwargs['detector_id']

      return Response({"success": True, "error": ""})

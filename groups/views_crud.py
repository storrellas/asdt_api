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

class GroupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    groupToAdd = serializers.CharField(max_length=200, required=False)


class GroupView(viewsets.ViewSet):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def create(self, request):
      if request.user.role != 'ADMIN':
        return Response({"success": False, "data": "NOT_ALLOWED"})

      # Group serializer
      serializer = GroupSerializer(data=request.data)
      if serializer.is_valid() == False:
        print({'message': serializer.errors})
        return Response({'success': False, 'data': 'DATABASE_ERRORS'})
      data = serializer.validated_data

      try:
        # Create group
        group = Group.objects.create(name=data['name'])
        
        # Determine relations
        # NOTE: I would rename this parameter by parent
        if 'groupToAdd' in data:
          logger.info('Parent is specificed ' + data['groupToAdd'])
          parent_group = Group.objects.get(id=data['groupToAdd'])
          if request.user.is_allowed_group(parent_group) == False:
            return Response({"success": False, "error": "NOT_ALLOWED"})


          parent_group.childs.append(group)
          parent_group.save()
          group.parent = parent_group
          group.save()
        elif request.user.group is not None:
          logger.info('Parent is group from user requesting ...')
          request.user.group.childs.append(group)
          request.user.group.save()
          group.parent = request.user.group
          group.save()
        else:
          logger.info('Parent is None')

        return Response({'success': True, 'data': group.as_dict()})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": "DOES_NOT_EXIST"})

    # def list(self, request):
    #   return Response({'success': True, 'data': ''})

    def retrieve(self, request, pk=None):
      try:
        group = Group.objects.get(id=pk)
        if request.user.is_allowed_group(group) == False:
          return Response({"success": False, "error": "NOT_ALLOWED"})

        return Response({"success": True, "data": group.as_dict()})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": "DOES_NOT_EXIST"})

    def update(self, request, pk=None):
      # Check role
      if request.user.role != 'ADMIN':
        return Response({"success": False, "data": "NOT_ALLOWED"})


      try:
        group = Group.objects.get(id=pk)
        if request.user.is_allowed_group(group) == False:
          return Response({"success": False, "error": "NOT_ALLOWED"})


        # Update parent
        # NOTE: I would rename this parameter by parent
        if 'newParent' in request.data:
          parent_group = Group.objects.get(id=request.data['newParent'])
          if request.user.group == group or request.user.group.is_parent_of(group):
            pass
          else:
            return Response({"success": False, "error": "NOT_ALLOWED"})

          # Remove group from old parent
          group.parent.childs.remove(group)
          group.parent.save()

          # Set new configuration
          group.parent = parent_group
          group.save()
          parent_group.childs.append(group)
          parent_group.save()


        # Update operation
        group.name = request.data['name']
        group.save()

        return Response({"success": True, "data": group.as_dict()})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": "DOES_NOT_EXIST"})

    def delete(self, request, pk=None):
      # Check role
      if request.user.role != 'ADMIN':
        return Response({"success": False, "data": "NOT_ALLOWED"})

      try:
        group = Group.objects.get(id=pk)
        if request.user.is_allowed_group(group) == False:
          return Response({"success": False, "error": "NOT_ALLOWED"})

        # Do not remove if root group
        if 'hasGroup' in group and group.hasGroup == True and group.parent is None:
          return Response({"success": False, "data": "CANNOT_REMOVE_ROOT_GROUP"})

        # Delete operation
        # if 'recursive' in request.query_params:
        #   group.delete_recursive()  
        # else:
        #   group.delete()
        # Remove group from childs in parent
        group.parent.childs.remove(group)
        group.parent.save()
        # Delete grouip recursively
        group.delete_recursive()

        return Response({"success": True, "data": ""})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": "DOES_NOT_EXIST"})




class GroupAllView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def get(self, request):

      # Check whether current user hasGroup
      if request.user.hasGroup == False:
        return Response({"success": False, "error": "THE_USER_HAS_NO_GROUP"})

      if request.user.role == 'ADMIN':
        group_list = request.user.group.get_full_children()
        group_list.append(request.user.group)
      elif request.user.role == 'VIEWER' or request.user.role == 'EMPOWERED':
        group_list = [request.user.group]


      # Generate dict
      data_dict = []
      for group in group_list:
        data_dict.append(group.as_dict())
      return Response({"success": True, "data": data_dict})
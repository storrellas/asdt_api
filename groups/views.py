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

from .models import *

logger = get_logger()

class GroupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    parent = serializers.CharField(max_length=200, required=False)

class GroupViewset(viewsets.ViewSet):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def create(self, request):

      try:
        if request.user.role != User.ADMIN:
          raise APIException('NOT_ALLOWED')

        # Group serializer
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid() == False:
          print({'message': serializer.errors})
          raise APIException(str(serialiezer.errors))
        data = serializer.validated_data

        # Create group
        group = Group.objects.create(name=data['name'])
        
        # Determine relations
        if 'parent' in data:
          logger.info('Parent is specificed ' + data['parent'])
          parent_group = Group.objects.get(id=data['parent'])
          if request.user.is_allowed_group(parent_group) == False:
            raise APIException("NOT_ALLOWED")

          group.parent = parent_group
          group.save()
        elif request.user.group is not None:
          logger.info('Parent is group from user requesting ...')
          group.parent = request.user.group
          group.save()
        else:
          logger.info('Parent is None')

        return Response(group.as_dict())
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # def list(self, request):
    #   return Response({'success': True, 'data': ''})

    def retrieve(self, request, pk=None):
      try:
        group = Group.objects.get(id=pk)
        if request.user.is_allowed_group(group) == False:
          raise APIException("NOT_ALLOWED")

        return Response(group.as_dict())
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
      try:
        # Check role
        if request.user.role != User.ADMIN:
          raise APIException("NOT_ALLOWED")
        
        # Check allowed group
        group = Group.objects.get(id=pk)
        if request.user.is_allowed_group(group) == False:
          raise APIException("NOT_ALLOWED")


        # Update parent
        if 'parent' in request.data:
          parent_group = Group.objects.get(id=request.data['parent'])
          if request.user.group == group or request.user.group.is_parent_of(group):
            pass
          else:
            raise APIException("NOT_ALLOWED")

          # Set new configuration
          group.parent = parent_group
          group.save()

        # Update operation
        group.name = request.data['name']
        group.save()

        return Response(group.as_dict())
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
      try:
        # Check role
        if request.user.role != User.ADMIN:
          raise APIException("NOT_ALLOWED")

        # Check allowed group
        group = Group.objects.get(id=pk)
        if request.user.is_allowed_group(group) == False:
          raise APIException("NOT_ALLOWED")

        # Do not remove if root group
        if 'hasGroup' in group and group.hasGroup == True and group.parent is None:
          raise APIException("CANNOT_REMOVE_ROOT_GROUP")

        # Delete operation
        group.delete_recursive()

        return Response(status=status.HTTP_204_NO_CONTENT)
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='groups')
    def groups(self, request, pk=None):
      try:
        group = Group.objects.get(id=pk)
        if request.user.is_allowed_group(group) == False:
          raise APIException("NOT_ALLOWED")

        # Generate data
        data = []
        for group in Group.objects.filter(parent=group.id):
          data.append(group.as_dict())        

        return Response(data)
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GroupAllView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def get(self, request):

      # Check whether current user hasGroup
      if request.user.hasGroup == False:
        return Response({"success": False, "error": "THE_USER_HAS_NO_GROUP"})

      if request.user.role == User.ADMIN:
        group_list = request.user.group.get_full_children()
        group_list.append(request.user.group)
      elif request.user.role == 'VIEWER' or request.user.role == 'EMPOWERED':
        group_list = [request.user.group]

      # Generate dict
      data_dict = []
      for group in group_list:
        data_dict.append(group.as_dict())
      return Response(data_dict)

class GroupUserViewset(viewsets.ViewSet):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
      try:
        group = Group.objects.get(id=kwargs['group_id'])
        if request.user.is_allowed_group(group) == False:
          raise APIException("NOT_ALLOWED")

        # Generate data
        data = []       
        for user in User.objects.filter(group=group):
           data.append(user.as_dict())

        return Response(data)
      except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
      """
      Adds user to group
      """
      try:
        # TODO: Put all this logic into a function
        if request.user.role != 'ADMIN':
          raise APIException("NOT_ALLOWED")
        
        # Get instances
        group = Group.objects.get(id=kwargs['group_id'])
        user = User.objects.get(id=kwargs['pk'])

        # Check whether request user has id
        if request.user.group is None:
          raise APIException("GROUP_ID_NOT_FOUND")

        # Check permissions
        if request.user.group.is_parent_of( group ):
          pass
        elif request.user.group == group and user.role == User.ADMIN:
          # If targeted user is ADMIN do not allow to modify group
          raise APIException("NOT_ALLOWED")
        else:
          raise APIException("NOT_ALLOWED")

        # Add user to group
        user.group = group
        user.save()       

        return Response(user.as_dict())
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, *args, **kwargs):
      """
      Removes user from group
      """
      try:
        if request.user.role != User.ADMIN:
          raise APIException("NOT_ALLOWED")


        # Get instances
        group = Group.objects.get(id=kwargs['group_id'])
        user = User.objects.get(id=kwargs['pk'])
        # Check whether request user has id
        if request.user.group is None:
          raise APIException("GROUP_ID_NOT_FOUND")

        # Check permissions
        if request.user.group.is_parent_of( group ):
          pass
        elif request.user.group == group and user.role == User.ADMIN:
          # If targeted user is ADMIN do not allow to modify group
          raise APIException("NOT_ALLOWED")
        else:
          raise APIException("NOT_ALLOWED")

        # Remove user from group
        user.group = None
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
      except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

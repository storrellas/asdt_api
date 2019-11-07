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

# Project imports
from asdt_api.utils import get_logger
from asdt_api.authentication import *
from asdt_api.models import Location

from .models import *
#from .serializers import *

logger = get_logger()

class GroupView(viewsets.ViewSet):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def create(self, request):
      serializer = UserSerializer(data=request.data)
      if serializer.is_valid():
        data = serializer.validated_data

        # Add group if any
        group = None
        if 'group' in data:
          # Recover group
          try:
            group = Group.objects.get(id=data['group'])
          except Exception as e:
            logger.info("mytest")
            print(str(e))
            return Response({"success": False, "error": "WRONG_PARAMTERS"})

          # Check permissions
          success = False
          if data['role'] == 'ADMIN':
            success = request.user.group.is_parent_of(group)
          elif data['role'] == 'VIEWER' or data['role'] == 'EMPOWERED':
            if request.user.group.is_parent_of(group) or request.user.group == group:
              success = True
          else:
            success = True
          
          if success == False:
            return Response({"success": False, "error": "NOT_ALLOWED"})

        # Create user        
        user = User.objects.create(email=data['email'], name=data['name'], 
                                    role=data['role'], hasGroup=data['hasGroup'])
        user.set_password(data['password'])

        # Add group to user        
        if group is not None:
          user.group = group
          user.save()

          # Append to group
          group.users.append(user)
          group.save()


        # ObjectID to str
        user_dict = user.to_mongo().to_dict()
        user_dict['_id'] = str(user_dict['_id'])   
        if 'group' in user_dict:       
          user_dict['group'] = str(user_dict['group'])


        return Response({'success': True, 'data': user_dict } )
      else:
        print({'message': serializer.errors})
        return Response({'sucess': False, 'data': 'DATABASE_ERRORS'})

    def list(self, request):
      return Response({'sucess': True, 'data': ''})

    def retrieve(self, request, pk=None):
      return Response({'sucess': True, 'data': ''})

    def update(self, request, pk=None):
      return Response({'sucess': True, 'data': ''})

    def delete(self, request, pk=None):
      return Response({'sucess': True, 'data': ''})



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

class GroupUserView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
      """
      Adds user to group
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
 
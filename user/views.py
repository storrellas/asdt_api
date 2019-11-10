import bcrypt
import jwt
import time
import json

# pymongo
from bson.objectid import ObjectId
from bson import json_util
import mongoengine


# Django import
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
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

logger = get_logger()

class UserAuthenticateView(APIView):

    def post(self, request):
    
      if 'email' not in request.data or 'password' not in request.data:
        return Response({"success": False, "error": "WRONG_PARAMETERS"})

      # Checking password
      email = request.data['email']
      password = request.data['password']

      # Check whether user exists
      try:
        user = User.objects.get(email=email)
        if bcrypt.checkpw(password.encode(), user.password.encode()):

          # Generate payload
          iat = int(time.time()) 
          exp = int(time.time()) + 6 * 3600        
          payload = {
            'type': 'user',
            'id': str(user.id),
            'iss': 'ASDT', 
            'iat': iat,
            'exp': exp
          }
          encoded = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
          data = {
            'success': True,
            'data':{
              'token': encoded
            }
          }
          return Response(data)
        else:
          return Response({"success": False, "error": "WRONG_PASSWORD"})
      except Exception as e:
        print(e)
        return Response({"success": False, "error": "DOES_NOT_EXIST"})


class UserSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=200, required=False)
    password = serializers.CharField(max_length=72, required=False)
    name = serializers.CharField(max_length=200, required=False)
    role = serializers.ChoiceField(choices=['MASTER', 'ADMIN', 'EMPOWERED', 'VIEWER'], required=False)
    hasGroup = serializers.BooleanField(required=False)

class UserSerializerExtended(UserSerializer):
    group = serializers.CharField(max_length=200, required=False)



class UserViewset(viewsets.ViewSet):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, ASDTIsAdminPermission,)

    def list(self, request):
      
      try:
        if request.user.group.parent is None:
          queryset = User.objects.all()
        else:

          # Get groups assigned
          groups = request.user.group.get_full_children() 
          groups.append( request.user.group )        

          # Queryset
          group_list = [ item.id for item in groups ]

          queryset = User.objects.filter(group__in=group_list)

        # Generate response
        user_dict = []
        for item in queryset:
          user = item.as_dict()
          # Remove non-necessary
          del user['displayOptions']
          user_dict.append( user )

        return Response({ 'success': True, 'data': user_dict } )

      except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)})
      

    def retrieve(self, request, pk=None):

      # Get user
      queryset = User.objects.filter(id=pk)
      if len(queryset) != 1:
        logger.info("Retreived: " + str(len(queryset)))
        return Response({"success": False, "error": "NOT_FOUND"})
      
      # Get user instance
      user = queryset.first()
      if request.user.has_power_over(user) == False:
        return Response({"success": False, "error": "NOT_ALLOWED"})

      return Response({ 'success': True, 'data': user.as_dict() } )

    def create(self, request):
      
      serializer = UserSerializerExtended(data=request.data)
      if serializer.is_valid() == False:
        print({'message': serializer.errors})
        return Response({'success': False, 'data': 'DATABASE_ERRORS'})

      # Create user
      data = serializer.validated_data

      # Add group if any
      group = None
      if 'group' in data:
        # Recover group
        try:
          group = Group.objects.get(id=data['group'])
        except Exception as e:
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

      return Response({'success': True, 'data': user.as_dict() } )

    def update(self, request, pk=None):

      try:

        # Get user
        user = User.objects.get(id=pk)
        if request.user.has_power_over(user) == False:
          raise APIException("NOT_ALLOWED")

        # Update User
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
          data = serializer.validated_data
          user.update(**data)
          if 'password' in data:
            user.set_password(data['password'])
          if 'group' in request.data:    
            group = Group.objects.get(id=request.data['group'])
            if request.user.is_allowed_group(group):
              user.hasGroup = True
              user.group = group
              user.save()

              # Append to group
              group.users.append(user)
              group.save()
            else:
              raise APIException("NOT_ALLOWED")
          user.save()   

        # Generate response
        user = User.objects.get(id=pk)
        return Response({'success': True, 'data': user.as_dict() } )

      except Exception as e:
        print(str(e))
        return Response({'success': False, 'data': 'DATABASE_ERRORS'})

    def delete(self, request, pk=None):

      try:
       
        # Get user instance
        user = User.objects.get(id=pk)
        if request.user.has_power_over(user) == False:
          return Response({"success": False, "error": "NOT_ALLOWED"})

        # Remove user from group        
        user.group.users.remove(user)
        user.group.save()

        # Delete user
        user.delete()

        return Response({ 'success': True } )

      except Exception as e:
        print(str(e))
        return Response({'sucess': False, 'data': str(e)})

class UserMeView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def get(self, request):     
        return Response({'success': True, 'data': request.user.as_dict()})

class UserToolsView(APIView):

    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    allowed_tools = {
      'ADMIN': {
        'USER':    True, 'REAL_TIME': True, 'TOOLS':      True, 
        'FLIGHTS': True, 'LAYERS':    True, 'ALARM':      True,
        'STATS':   True, 'SETTING':   True, 'INHIBITORS': True
      },
      'EMPOWERED': {
        'USER':    True,  'REAL_TIME': True,  'TOOLS':      True, 
        'FLIGHTS': True,  'LAYERS':    False, 'ALARM':      True,
        'STATS':   False, 'SETTING':   False, 'INHIBITORS': True
      },
      'VIEWER': {
        'USER':    True,  'REAL_TIME': True,  'TOOLS':      True, 
        'FLIGHTS': True,  'LAYERS':    False, 'ALARM':      True,
        'STATS':   False, 'SETTING':   False, 'INHIBITORS': False
      }
    }

    def get(self, request):
      return Response({'success': True, 'data': self.allowed_tools[ request.user.role ]})

# class DisplayOptions(APIView):

#     authentication_classes = [ASDTAuthentication]
#     permission_classes = (IsAuthenticated,)

#     def displayOptionsResponse(self, displayOptions):
#       # Dump displayOptions
#       displayOptions_bson = json_util.dumps(displayOptions)
#       displayOptions_json = json.loads( displayOptions_bson )
      
#       print(displayOptions_json)

#       # JSON values
#       zone_json = displayOptions_json['zone']
#       circleZone_json = displayOptions_json['circleZone']
#       # Remove Id
#       for item in circleZone_json:
#         item.pop('_id', None)
#       print(displayOptions_json)
#       return {
#         'success': True,
#         'data': {
#           "mapType": displayOptions['mapType'],
#           "zone": zone_json,
#           "circleZone": circleZone_json
#         }
#       }

#     def displayOptionsUpdate(self, user, displayOptions):
#       # Update one
#       if 'mapType' in displayOptions:
#         db.users.update_one({'_id': user.data['_id']}, 
#                             {
#                               '$set':{'displayOptions.mapType': displayOptions['mapType']}
#                             })
#       if 'zone' in displayOptions:
#         db.users.update_one({'_id': user.data['_id']}, 
#                             {
#                               '$set':{'displayOptions.zone': displayOptions['zone']}
#                             })
#       if 'circleZone' in displayOptions:
#         db.users.update_one({'_id': user.data['_id']}, 
#                             {
#                               '$set':{'displayOptions.circleZone': displayOptions['circleZone']}
#                             })



#     def get(self, request):

#       # Prepare response
#       data = self.displayOptionsResponse(request.user.data['displayOptions'])
#       return Response(data)

#     def put(self, request):

#       # Update 
#       self.displayOptionsUpdate(request.user, request.data)

#       # Prepare response
#       user = db.users.find_one({'_id': request.user.data['_id']})
#       data = self.displayOptionsResponse(user['displayOptions'])
#       return Response(data)

#     def post(self, request):

#       # Update 
#       self.displayOptionsUpdate(request.user, request.data)

#       # Prepare response
#       user = db.users.find_one({'_id': request.user.data['_id']})
#       data = self.displayOptionsResponse(user['displayOptions'])
#       return Response(data)




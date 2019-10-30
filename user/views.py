import bcrypt
import jwt
import time
import json

# pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import json_util


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

# Project imports
from asdt_api.utils import get_logger
from asdt_api.authentication import *
from asdt_api.models import Location

from .models import *
from .serializers import *

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




class UserViewset(viewsets.ViewSet):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,ASDTIsAdminPermission,)

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

      # List all users
      queryset = None
      if request.user.group.parent is None:
        queryset = User.objects.all()
      else:

        # Get groups assigned
        groups = []
        if request.user.group is not None:
          # Get referenced groups
          groups.extend( request.user.group.get_full_children() ) 
          # Add user group
          groups.append( request.user.group )

        # Get group List
        group_list = []
        for item in groups:
          group_list.append(item.id)

        # Queryset
        queryset = User.objects.filter(group__in=group_list)


      # Generate response
      user_dict = []
      for item in queryset:
        item = item.to_mongo().to_dict()
        item['_id'] = str(item['_id'])
        if 'group' in item:       
          item['group'] = str(item['group'])

        # Filtering items
        del item['displayOptions']
        del item['__v']
        del item['createdAt']
        del item['updatedAt']
        del item['password']

        user_dict.append( item )

      return Response({ 'success': True, 'data': user_dict } )

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

      # Generate response
      user_dict = []
      for item in queryset:
        item = item.to_mongo().to_dict()
        item['_id'] = str(item['_id'])
        if 'group' in item:       
          item['group'] = str(item['group'])

        # Filtering items
        del item['__v']
        del item['password']

        user_dict.append( item )

      user_dict = user_dict[0]
      return Response({ 'success': True, 'data': user_dict } )

    def update(self, request, pk=None):

      try:

        # Get user
        queryset = User.objects.filter(id=pk)
        if len(queryset) != 1:
          logger.info("Retreived: " + str(len(queryset)))
          return Response({"success": False, "error": "NOT_FOUND"})
        
        # Get user instance
        user = queryset.first()
        if request.user.has_power_over(user) == False:
          return Response({"success": False, "error": "NOT_ALLOWED"})

        # Update User
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
          data = serializer.validated_data
          user.email = data['email'] if 'email' in data else user.email
          user.name = data['name'] if 'name' in data else user.name
          user.role = data['role'] if 'role' in data else user.role
          if 'password' in data:
            user.set_password(data['password'])
          if 'group' in data:
            if data['group'] == "0":
              pass
            else:            
              target_group = Group.objects.get(id=data['group'])
              if target_group == request.user.group or request.user.group.is_parent_of(target_group):
                user.hasGroup = True
                user.group = target_group
          user.save()

        # Generate response
        user_dict = []
        for item in [user]:
          item = item.to_mongo().to_dict()
          item['_id'] = str(item['_id'])
          if 'group' in item:       
            item['group'] = str(item['group'])

          # Filtering items
          del item['__v']
          del item['password']

          user_dict.append( item )

        user_dict = user_dict[0]
        return Response({ 'success': True, 'data': user_dict } )

      except Exception as e:
        print(str(e))
        return Response({'sucess': False, 'data': 'DATABASE_ERRORS'})

    def delete(self, request, pk=None):

      try:

        # Get user
        queryset = User.objects.filter(id=pk)
        if len(queryset) != 1:
          logger.info("Retreived: " + str(len(queryset)))
          return Response({"success": False, "error": "NOT_FOUND"})
        
        # Get user instance
        user = queryset.first()
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
        return Response({'sucess': False, 'data': 'DATABASE_ERRORS'})

class UserMeView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def get(self, request):
        data = {
          'success': True,
          'data': {
            'id': str(request.user.id),
            'email': request.user.email,
            'name': request.user.name,
            'detectors' : [],
            'inhibitors' : [],
            'role' : request.user.role,
          }
        } 

        
        return Response(data)

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
      data = {
        'success': True,
        'data': self.allowed_tools[ request.user.role ]
      }
      return Response(data)

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




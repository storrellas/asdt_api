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
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.permissions import IsAuthenticated

# Project imports
from asdt_api.utils import get_logger
from asdt_api.authentication import *

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




class UserView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,ASDTIsAdminPermission,)

    def post(self, request):
      serializer = UserSerializer(data=request.data)
      if serializer.is_valid():
        data = serializer.validated_data

        # Create user
        user = User.objects.create(email=data['email'], name=data['name'], role=data['role'])
        user.set_password(data['password'])

        # Add group if any
        if data['hasGroup']:
          ## Checking whether group is valid
          ## Checking whether group is valid
          ## Checking whether group is valid

          try:
            group = Group.objects.get(id=data['group'])
            user.hasGroup = True
            user.group = group
            user.save()
          except Exception as e:
            logger.info("mytest")
            print(str(e))
            return Response({"success": False, "error": "WRONG_PARAMTERS"})
        
        # ObjectID to str
        user_dict = user.to_mongo().to_dict()
        user_dict['_id'] = str(user_dict['_id'])   
        if 'group' in user_dict:       
          user_dict['group'] = str(user_dict['group'])

        ## Adding here logic to create user
        print("Logic to create user", serializer.validated_data) 
        print(user_dict)       
        return Response({'success': True, 'data': user_dict } )
      else:
          print({'message': serializer.errors})
          return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


      

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




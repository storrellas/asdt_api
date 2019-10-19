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
from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.permissions import IsAuthenticated

# Project imports
from asdt_api.utils import get_logger

logger = get_logger()

# Create MongoClient
client = MongoClient('localhost', 27017)
db = client.asdt

class ASDTUser:
  data = {}
  def __init__(self, data):
    self.data = data

  def is_authenticated(self):
    return True

class ASDTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):

      # Decoded header
      authorization_header = request.META.get('HTTP_AUTHORIZATION')
      encoded_jwt = authorization_header.split(' ')[1]
      try:
        decoded_jwt = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=['HS256'])
        user = db.users.find_one({'_id':ObjectId(decoded_jwt['id'])})
        if user is None:
          return (None, None)
        else:
          return (ASDTUser(data=user), None)
      except Exception as e:
        print(e)
        return (None, None)
      except jwt.ExpiredSignatureError as e:
        print("Expired ", str(e))
        return (None, None)

      


class Authenticate(APIView):

    def post(self, request):
      if 'email' not in request.data or 'password' not in request.data:
        return Response({"success": False, "error": "WRONG_PARAMETERS"})

      # Checking password
      email = request.data['email']
      password = request.data['password']
      user = db.users.find_one({'email':email})
      if bcrypt.checkpw(password.encode(), user['password'].encode()):

        # Generate payload
        iat = int(time.time()) 
        exp = int(time.time()) + 6 * 3600        
        payload = {
          'type': 'user',
          'id': str(user['_id']),
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

class UserInfo(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def get(self, request):
        data = {
          'success': True,
          'data': {
            'id': str(request.user.data['_id']),
            'email': request.user.data['email'],
            'name': request.user.data['name'],
            'detectors' : [],
            'inhibitors' : [],
            'role' : request.user.data['role'],
          }
        } 
        logger.info("In view")
        print(request.user.data)
        return Response(data)

class AllowedTools(APIView):

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
        'data': self.allowed_tools[ request.user.data['role'] ]
      }
      return Response(data)

class DisplayOptions(APIView):

    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def displayOptionsResponse(self, displayOptions):
      # Dump displayOptions
      displayOptions_bson = json_util.dumps(displayOptions)
      displayOptions_json = json.loads( displayOptions_bson )
      
      print(displayOptions_json)

      # JSON values
      zone_json = displayOptions_json['zone']
      circleZone_json = displayOptions_json['circleZone']
      # Remove Id
      for item in circleZone_json:
        item.pop('_id', None)
      print(displayOptions_json)
      return {
        'success': True,
        'data': {
          "mapType": displayOptions['mapType'],
          "zone": zone_json,
          "circleZone": circleZone_json
        }
      }

    def displayOptionsUpdate(self, user, displayOptions):
      # Update one
      if 'mapType' in displayOptions:
        db.users.update_one({'_id': user.data['_id']}, 
                            {
                              '$set':{'displayOptions.mapType': displayOptions['mapType']}
                            })
      if 'zone' in displayOptions:
        db.users.update_one({'_id': user.data['_id']}, 
                            {
                              '$set':{'displayOptions.zone': displayOptions['zone']}
                            })
      if 'circleZone' in displayOptions:
        db.users.update_one({'_id': user.data['_id']}, 
                            {
                              '$set':{'displayOptions.circleZone': displayOptions['circleZone']}
                            })



    def get(self, request):

      # Prepare response
      data = self.displayOptionsResponse(request.user.data['displayOptions'])
      return Response(data)

    def put(self, request):

      # Update 
      self.displayOptionsUpdate(request.user, request.data)

      # Prepare response
      user = db.users.find_one({'_id': request.user.data['_id']})
      data = self.displayOptionsResponse(user['displayOptions'])
      return Response(data)

    def post(self, request):

      # Update 
      self.displayOptionsUpdate(request.user, request.data)

      # Prepare response
      user = db.users.find_one({'_id': request.user.data['_id']})
      data = self.displayOptionsResponse(user['displayOptions'])
      return Response(data)




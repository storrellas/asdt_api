import bcrypt
import jwt
import time

# pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps


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
    def get(self, request):
        data = {
          'success': True,
          'data':{
            'token': '123'
          }
        }
        return Response(data)
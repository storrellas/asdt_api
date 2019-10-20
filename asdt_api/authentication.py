import jwt

from bson.objectid import ObjectId

# Django import 
from django.conf import settings

# rest framework import
from rest_framework import authentication

from user.models import *

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
        user = User.objects.get(id=decoded_jwt['id'])
        return(user, None)
      except Exception as e:
        print(e)
        return (None, None)
      except jwt.ExpiredSignatureError as e:
        print("Expired ", str(e))
        return (None, None)
import jwt

from bson.objectid import ObjectId

# Django import 
from django.conf import settings

# rest framework import
from rest_framework import authentication, permissions

# Project includes
from user.models import *
from .utils import get_logger

logger = get_logger()

class ASDTUser:
  data = {}
  def __init__(self, data):
    self.data = data

  def is_authenticated(self):
    return True

class ASDTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
      try:
        # Decoded header
        authorization_header = request.META.get('HTTP_AUTHORIZATION')
        encoded_jwt = authorization_header.split(' ')[1]

        decoded_jwt = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=['HS256'])       
        user = User.objects.get(id=decoded_jwt['id'])
        return(user, None)
      except Exception as e:
        logger.info("Exception " + str(e))
        return (None, None)
      except jwt.ExpiredSignatureError as e:
        logger.info("Expired " + str(e))
        return (None, None)

class ASDTIsAdminPermission(permissions.BasePermission):

    def has_permission(self, request, view):
      if request.user.role == 'ADMIN':
        return True
      else:
        return False
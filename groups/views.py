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

class GroupAllView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,ASDTIsAdminPermission,)

    def get(self, request):
      print("-----------SERGI ------------------")
      return Response({"success": True, "error": "WRONG_PASSWORD"})


      # if 'email' not in request.data or 'password' not in request.data:
      #   return Response({"success": False, "error": "WRONG_PARAMETERS"})

      # # Checking password
      # email = request.data['email']
      # password = request.data['password']

      # # Check whether user exists
      # try:
      #   user = User.objects.get(email=email)
      #   if bcrypt.checkpw(password.encode(), user.password.encode()):

      #     # Generate payload
      #     iat = int(time.time()) 
      #     exp = int(time.time()) + 6 * 3600        
      #     payload = {
      #       'type': 'user',
      #       'id': str(user.id),
      #       'iss': 'ASDT', 
      #       'iat': iat,
      #       'exp': exp
      #     }
      #     encoded = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
      #     data = {
      #       'success': True,
      #       'data':{
      #         'token': encoded
      #       }
      #     }
      #     return Response(data)
      #   else:
      #     return Response({"success": False, "error": "WRONG_PASSWORD"})
      # except Exception as e:
      #   print(e)
      #   return Response({"success": False, "error": "DOES_NOT_EXIST"})
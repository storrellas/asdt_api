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
        item = {}
        item['id'] = str(group.id)
        item['name'] = str(group.name)
        item['parent'] = str(group.parent.id) if group.parent is not None else 'undef'
        item['users'] = []
        for user in group.users:
          item['users'].append(str(user.id))
        item['childs'] = []
        for group_child in group.childs:
          item['childs'].append(str(group_child.id))
        
        detectors_list = []
        for detector in group.devices.detectors:
          detectors_list.append( str(detector.id) )
        inhibitor_list = []
        for inhibitor in group.devices.inhibitors:
          inhibitor_list.append( str(inhibitor.id) )
        zones_list = []
        for zone in group.devices.zones:
          zones_list.append( str(zone.id) )
        friend_drone_list = []
        for friend_drone in group.devices.friendDrones:
          friend_drone_list.append( str(friend_drone.id) )
        item['devices'] = {
          'detectors' : detectors_list,
          'inhibitors' : inhibitor_list,
          'zones' : zones_list,
          'friendDrones' : friend_drone_list,
        }

        data_dict.append(item)

      return Response({"success": True, "data": data_dict})


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
import os

from django.shortcuts import render
from django.utils.encoding import smart_str
from django.http import HttpResponse
from django.views import View
from django.conf import settings

# rest framework import
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated

# Project imports
from asdt_api.authentication import ASDTIsAdminOrMasterPermission, ASDTAuthentication
from asdt_api.views import DeviceViewset
from bson.objectid import ObjectId
from .models import *

class DroneModelView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, )


    def get(self, request, log_id = None):
        queryset = DroneModel.objects.fields(id=0).all()

        # Transform to queryset
        data = []
        for item in queryset:
          data.append(item.as_dict())
        data = { 
            'success': True,
            'data': data
        } 
        return Response(data)


class DroneSerializer(serializers.Serializer):
    sn = serializers.CharField(max_length=200, required=False)
    owner = serializers.CharField(max_length=72, required=False)
    hide = serializers.BooleanField(required=False)

class DroneViewset(DeviceViewset):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated, ASDTIsAdminOrMasterPermission)

    model = Drone
    serializer = DroneSerializer

    def get_id_list_allowed(self, request):
      """
      Returns all ids allowed for current user
      """
      id_list = []
      for item in self.devices.friendDrones:
        id_list.append(str(item.fetch().id) )
      return id_list

    def get_groups(self, instance):
      """
      Returns all groups associated to instance
      """
      return Group.objects.filter(devices__friendDrones__in=[instance.id])

    # def create(self, request):
    #   return Response({"success": True, "data": "create"})

    # def list(self, request):
    #   """
    #   Retrieve all inhibitors 
    #   """
    #   return super().list(request)

    # def retrieve(self, request, pk=None):
    #   return Response({"success": True, "data": "retrieve"})

    # def update(self, request, pk=None):
    #   return Response({"success": True, "data": "update"})

    # def delete(self, request, pk=None):
    #   return Response({"success": True, "data": "delete"})

# class DroneModelImgView(APIView):
#     authentication_classes = [ASDTAuthentication]
#     permission_classes = (IsAuthenticated,)

#     def get(self, request, model_id = None):
#       file_path = '{}/drones/model/{}.png'.format(settings.MEDIA_ROOT, model_id)
#       if os.path.exists(file_path):
#         with open(file_path, 'rb') as fh:
#           response = HttpResponse(fh.read(), content_type="image/png")
#           response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
#           return response
#       return HttpResponse('failed')
      

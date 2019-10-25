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
from rest_framework.permissions import IsAuthenticated

# Project imports
from asdt_api.authentication import ASDTAuthentication
from bson.objectid import ObjectId
from .models import *

class DroneModelView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def get(self, request, log_id = None):
        queryset = DroneModel.objects.fields(id=0).all()

        # Transform to queryset
        data = []
        for item in queryset:
          data.append(item.to_mongo().to_dict())
        data = { 
            'success': True,
            'data': data
        } 
        return Response(data)


class DroneModelImgView(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def get(self, request, model_id = None):
      file_path = '{}/{}.png'.format(settings.MEDIA_ROOT, model_id)
      if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
          response = HttpResponse(fh.read(), content_type="image/png")
          response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
          return response
      return HttpResponse('failed')
      

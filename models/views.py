from django.shortcuts import render

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

class Model(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def get(self, request, log_id = None):
        model_list = ModelDetector.objects.exclude('id').all()
        print(model_list.as_pymongo())
        print(type(model_list.as_pymongo()))
        print(type(model_list.as_pymongo().to_mongo()))
        data = { 
            'success': True,
            'data': model_list.as_pymongo()
        } 
        return Response(data)


class ModelImg(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def get(self, request, log_id = None):

        data = { 
            'success': True,
        } 
        return Response(data)

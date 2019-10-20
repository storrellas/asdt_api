import json

# Python imports
from datetime import datetime,timedelta

# Django imports
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
from .models import *

class LogById(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def post(self, request, log_id = None):
        print('logbyid')
        data = { 'success': True } 
        return Response(data)


class LogByPage(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        # Get dateIni / dateFin / sn
        # query = {
        #     'dateIni': { '$gt': datetime.now() - timedelta(days=30) },
        #     'dateIni': { '$lt': datetime.now() },
        # }
        if 'dateIni' in request.data:
            dateIni = request.data['dateIni']
        if 'dateFin' in request.data:
            dateFin = request.data['dateIni']
        if 'sn' in request.data:
            sn = request.data['sn']

        # # Querying all objects
        # # for item in Log.objects:
        # #     print(item.to_mongo())
        # #print(Log.objects.all().as_pymongo())

        # # sons = [ob.to_mongo() for ob in Log.objects.all()]
        # # for son in sons:
        # #     print(str(son.to_dict()))
        # queryset_json = Log.objects.all().to_json()
        # queryset_dict = json.loads(queryset_json)
        pipeline = [
            {
                "$project": {
                    "_id": {  "$toString": "$_id" },
                    "dateIni": { "$dateToString": { "format": "%Y-%m-%d", "date": "$dateIni" } },
                    "dateFin": { "$dateToString": { "format": "%Y-%m-%d", "date": "$dateIni" } },
                    "productId": { "$ifNull": [ "$productId", "undef" ] },
                    "sn": { "$ifNull": [ "$sn", "undef" ] },
                    "model": { "$ifNull": [ "$model", "undef" ] },
                    "owner": { "$ifNull": [ "$owner", "undef" ] },
                    "maxHeight": { "$ifNull": [ "$maxHeight", "undef" ] },
                    "distanceTraveled": { "$ifNull": [ "$distanceTraveled", "undef" ] },
                    "distanceToDetector": { "$ifNull": [ "$distanceToDetector", "undef" ] },
                    "driverLocation": { "$ifNull": [ "$driverLocation", "undef" ] },
                    "homeLocation": { "$ifNull": [ "$homeLocation", "undef" ] },
                    "id": {  "$toString": "$_id" },
                }
            }
        ]
        # See https://docs.mongodb.com/manual/reference/operator/aggregation/ifNull/
        #{ $ifNull: [ "$description", "Unspecified" ] }
        log_dict = Log.objects.aggregate(*pipeline)

        data = { 
            'success': True,
            'data': log_dict
         } 
        return Response(data)

class GetFlightAll(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def post(self, request):
        print(request.user.data)
        data = { 'success -all': True } 
        return Response(data)        
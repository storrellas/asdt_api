import json

# Python imports
from datetime import datetime, timedelta

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
from bson.objectid import ObjectId
from .models import *
from user.models import *

class LogById(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def get(self, request, log_id = None):

        # Get queryset
        queryset = Log.objects.filter(id=log_id)
        if len(queryset) != 1:
            return Response({"success": False, "error": "NOT_FOUND"})


        # # Allowed detector list
        # detector_list_for_user = []
        # allowed = False
        # for detector in request.user.group.devices.detectors:
        #     detector_list_for_user.append( detector.fetch().id )

        # log = queryset.first()        
        # for detector in log.detectors:

        # #queryset = queryset.filter(detectors__in=[detector_list_for_user])


        
        
        if len(queryset) != 1:
            return Response({"success": False, "error": "NOT_FOUND"})


        # Prepare results
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
                    "route": { "lat": 1, "lon": 1, "aHeight": 1, "fHeight": 1, "time": { "$dateToString": { "format": "%Y-%m-%dT%H:%M:%S:%L", "date": "$dateIni" } }  },
                    "detectors" : { "id": { "$toString": "$_id" } },
                }
            }
        ]

        # Iterate cursor
        log_dict = queryset.aggregate(*pipeline)
        data = log_dict.next()
        data = { 
            'success': True,
            'data': data
        } 
        return Response(data)





class LogByPage(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    page_size = 200

    def post(self, request):

        # Get dateIni / dateFin / sn / page
        dateIni = datetime.datetime.now() - timedelta(days=4)
        if 'dateIni' in request.data:
            dateIni = datetime.datetime.strptime(request.data['dateIni'], "%Y-%m-%dT%H:%M:%S.%fZ")
        dateFin = datetime.datetime.now()
        if 'dateFin' in request.data:
            dateFin = datetime.datetime.strptime(request.data['dateFin'], "%Y-%m-%dT%H:%M:%S.%fZ")
        sn = None
        if 'sn' in request.data:
            sn = request.data['sn']
        page = 0
        if 'page' in request.data:
            page = request.data['page']

        # Select query to apply
        query = { "$and": [ {"dateIni": {"$gt": dateIni }}, {"dateFin": {"$lte": dateFin }}] }
        if sn is not None:
            query = { "$and": [ {"dateIni": {"$gt": dateIni }}, {"dateFin": {"$lte": dateFin }}, { "sn": sn }] }

        queryset = Log.objects.filter(dateIni__gt=dateIni, dateFin__lte=dateFin)
        if sn is not None:
            queryset = queryset.filter(sn=sn)

        # # Allowed detector list
        # detector_list_for_user = []        
        # for detector in request.user.group.devices.detectors:
        #     detector_list_for_user.append( detector.fetch().id )
        # print(detector_list_for_user)
        # queryset = queryset.filter(detectors__in=[detector_list_for_user])

        # ############################
        # # user = User.objects.get(email='admin@asdt.eu')
        # # user.group
        # # queryset = Log.objects.all()
        # # Allowed detector list
        # detector_list_for_user = []
        # for detector in request.user.group.devices.detectors:
        #     detector_list_for_user.append( str(detector.fetch().id) )
        # print(detector_list_for_user)
        # queryset = queryset.filter(detectors__in=[detector_list_for_user])
        # for item in queryset:
        #     print(item)
        # ############################

        # queryset = Log.objects.all()


        # Apply paging        
        queryset = queryset.skip(self.page_size * page)
        queryset = queryset.limit(self.page_size)


        # Querying all objects
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
        cursor = queryset.aggregate(*pipeline)
        data = { 
            'success': True,
            'data': cursor
         } 
        return Response(data)

# class GetFlightAll(APIView):
#     authentication_classes = [ASDTAuthentication]
#     permission_classes = (IsAuthenticated,)

#     def post(self, request):
#         print(request.user.data)
#         data = { 'success -all': True } 
#         return Response(data)        
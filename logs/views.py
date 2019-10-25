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

    def get_allowed(self, user, queryset):
        # Allowed detector list for user
        detector_set_for_user = set()
        for detector in user.group.devices.detectors:
            detector_set_for_user.add( str(detector.fetch().id) )

        # Check logs allowed
        log_allowed = []
        for log in queryset:
            detector_set = set()
            for detector in log.detectors:
                detector_set.add(str(detector.id))
            if len( detector_set & detector_set_for_user ) > 0:
                log_allowed.append(log['id'])
        return log_allowed

    def get(self, request, log_id = None):

        # Get queryset
        queryset = Log.objects.filter(id=log_id)
        if len(queryset) != 1:
            return Response({"success": False, "error": "NOT_FOUND"})


        # # Apply filtering            
        # log_allowed = self.get_allowed(request.user, queryset)
        # queryset = queryset.filter(id__in=log_allowed)
        # if queryset.count() == 0:
        #     return Response({"success": False, "error": "NOT_ALLOWED"})


        # Prepare results
        pipeline = [
            {
                "$project": {
                    #"_id": {  "$toString": "$_id" },
                    "dateIni": { "$dateToString": { "format": "%Y-%m-%dT%H:%M:%S", "date": "$dateIni" } },
                    "dateFin": { "$dateToString": { "format": "%Y-%m-%dT%H:%M:%S", "date": "$dateIni" } },
                    "productId": { "$ifNull": [ "$productId", "undef" ] },
                    "sn": { "$ifNull": [ "$sn", "undef" ] },
                    "model": { "$ifNull": [ "$model", "undef" ] },
                    "owner": { "$ifNull": [ "$owner", "undef" ] },
                    "maxHeight": { "$ifNull": [ "$maxHeight", "undef" ] },
                    "distanceTraveled": { "$ifNull": [ "$distanceTraveled", "undef" ] },
                    "distanceToDetector": { "$ifNull": [ "$distanceToDetector", "undef" ] },
                    "driverLocation": { "$ifNull": [ "$driverLocation", "undef" ] },
                    "homeLocation": { "$ifNull": [ "$homeLocation", "undef" ] },
                    #"id": {  "$toString": "$_id" },
                    #"detectors" : { "id": { "$toString": "$_id" } },
                    "detectors" : { "id": { "$ifNull": [ "$_id", "undef" ] } },
                    "route": { "lat": 1, "lon": 1, "aHeight": 1, "fHeight": 1, "time": { "$dateToString": { "format": "%Y-%m-%dT%H:%M:%S:%L", "date": "$dateIni" } }  },
                }
            }
        ]

        # Iterate cursor
        cursor = queryset.aggregate(*pipeline)
        data = cursor.next()

        # NOTE: This needs to be improved
        data['_id'] = str(data['_id'])
        data['id'] = str(data['_id'])
        detectors_list = []
        for detector in data['detectors']:
            detectors_list.append(str(detector['id']))
        data['detectors'] = detectors_list        

        data = { 
            'success': True,
            'data': data
        } 
        return Response(data)


class LogByPage(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    page_size = 200

    def get_allowed(self, user, queryset):
        # Allowed detector list for user
        detector_set_for_user = set()
        for detector in user.group.devices.detectors:
            detector_set_for_user.add( str(detector.fetch().id) )

        # Check logs allowed
        log_allowed = []
        for log in queryset:
            detector_set = set()
            for detector in log.detectors:
                detector_set.add(str(detector.id))
            if len( detector_set & detector_set_for_user ) > 0:
                log_allowed.append(log['id'])
        return log_allowed

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


        # Apply filtering            
        log_allowed = self.get_allowed(request.user, queryset)
        print(log_allowed)
        # queryset = queryset.filter(id__in=log_allowed)
        # if queryset.count() == 0:
        #     return Response({"success": False, "error": "NOT_ALLOWED"})

        # Apply paging        
        queryset = queryset.skip(self.page_size * page)
        queryset = queryset.limit(self.page_size)

        # Querying all objects
        pipeline = [
            {
                "$project": {
                    #"_id": {  "$toString": "$_id" },
                    "dateIni": { "$dateToString": { "format": "%Y-%m-%dT%H:%M:%S", "date": "$dateIni" } },
                    "dateFin": { "$dateToString": { "format": "%Y-%m-%dT%H:%M:%S", "date": "$dateIni" } },
                    "productId": { "$ifNull": [ "$productId", "undef" ] },
                    "sn": { "$ifNull": [ "$sn", "undef" ] },
                    "model": { "$ifNull": [ "$model", "undef" ] },
                    "owner": { "$ifNull": [ "$owner", "undef" ] },
                    "maxHeight": { "$ifNull": [ "$maxHeight", "undef" ] },
                    "distanceTraveled": { "$ifNull": [ "$distanceTraveled", "undef" ] },
                    "distanceToDetector": { "$ifNull": [ "$distanceToDetector", "undef" ] },
                    "driverLocation": { "$ifNull": [ "$driverLocation", "undef" ] },
                    "homeLocation": { "$ifNull": [ "$homeLocation", "undef" ] },
                    #"id": {  "$toString": "$_id" },
                    #"detectors" : { "id": { "$toString": "$_id" } },
                    "detectors" : { "id": { "$ifNull": [ "$_id", "undef" ] } },
                }
            }
        ]
        cursor = queryset.aggregate(*pipeline)        

        # NOTE: This needs to be improved
        data = []
        for item in cursor:
            item['_id'] = str(item['_id'])
            item['id'] = str(item['_id'])
            detectors_list = []
            for detector in item['detectors']:
                detectors_list.append(str(detector['id']))
            item['detectors'] = detectors_list
            data.append(item)
        data = { 
            'success': True,
            'data': data
         } 
        return Response(data)

# class GetFlightAll(APIView):
#     authentication_classes = [ASDTAuthentication]
#     permission_classes = (IsAuthenticated,)

#     def post(self, request):
#         print(request.user.data)
#         data = { 'success -all': True } 
#         return Response(data)        
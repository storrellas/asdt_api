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

class LogById(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def get(self, request, log_id = None):

        pipeline = [
            {
                "$match": { "_id": ObjectId(log_id) }
            },
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
        log_dict = Log.objects.aggregate(*pipeline)
        data = { 
            'success': True,
            'data': log_dict 
        } 
        return Response(data)


class LogByPage(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        # Get dateIni / dateFin / sn
        dateIni = datetime.datetime.now() - timedelta(days=4)
        if 'dateIni' in request.data:
            dateIni = datetime.datetime.strptime(request.data['dateIni'], "%Y-%m-%dT%H:%M:%S.%fZ")
        dateFin = datetime.datetime.now()
        if 'dateFin' in request.data:
            dateFin = datetime.datetime.strptime(request.data['dateFin'], "%Y-%m-%dT%H:%M:%S.%fZ")
        sn = None
        if 'sn' in request.data:
            sn = request.data['sn']

        # Select query to apply
        query = { "$and": [ {"dateIni": {"$gt": dateIni }}, {"dateFin": {"$lte": dateFin }}] }
        if sn is not None:
            query = { "$and": [ {"dateIni": {"$gt": dateIni }}, {"dateFin": {"$lte": dateFin }}, { "sn": sn }] }

        # Querying all objects
        pipeline = [
            {
                "$match": query
            },
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
        log_dict = Log.objects.aggregate(*pipeline)
        data = { 
            'success': True,
            'data': log_dict
         } 
        return Response(data)

# class GetFlightAll(APIView):
#     authentication_classes = [ASDTAuthentication]
#     permission_classes = (IsAuthenticated,)

#     def post(self, request):
#         print(request.user.data)
#         data = { 'success -all': True } 
#         return Response(data)        
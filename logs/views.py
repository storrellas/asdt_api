import json

# Python imports
from datetime import datetime, timedelta

# Django imports
from django.shortcuts import render
from django.http import HttpResponse

# rest framework import
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, permission_classes

# Project imports
from asdt_api.authentication import ASDTAuthentication
from bson.objectid import ObjectId
from .models import *
from user.models import *
from asdt_api.utils import get_logger

logger = get_logger()

class LogViewSet(viewsets.ViewSet):

    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)

    page_size = 200

    def get_allowed(self, user, queryset):
        # Check existance of group
        if user.group is None:
            return []
        if user.group.devices is None:
            return []
        if user.group.devices.detectors is None:
            return []

        # Allowed detector list for user
        detector_set_for_user = set()
        #for detector in user.group.devices.detectors:
        devices = user.group.get_full_devices()
        for detector in devices.detectors:
            detector_set_for_user.add( str(detector.fetch().id) )

        # Check logs allowed
        log_allowed = []
        for log in queryset:
            detector_set = set()
            for detector in log.detectors:
                detector_set.add(str(detector.id))
            # Check detector_set_for_user
            #print('detector_set', log.id, detector_set)

            if len( detector_set & detector_set_for_user ) > 0:
                log_allowed.append(log['id'])
        return log_allowed

    def list(self, request):

        # Get dateIni / dateFin / sn / page
        dateIni = datetime.datetime.now() - timedelta(days=4)
        if 'dateIni' in request.query_params:
            dateIni = datetime.datetime.strptime(request.query_params['dateIni'], "%Y-%m-%dT%H:%M:%S.%fZ")
        dateFin = datetime.datetime.now()
        if 'dateFin' in request.query_params:
            dateFin = datetime.datetime.strptime(request.query_params['dateFin'], "%Y-%m-%dT%H:%M:%S.%fZ")
        sn = self.request.query_params.get('sn', None)
        page = int(self.request.query_params.get('page', 0))

        # Select query to apply
        query = { "$and": [ {"dateIni": {"$gt": dateIni }}, {"dateFin": {"$lte": dateFin }}] }
        if sn is not None:
            query = { "$and": [ {"dateIni": {"$gt": dateIni }}, {"dateFin": {"$lte": dateFin }}, { "sn": sn }] }

        queryset = Log.objects.filter(dateIni__gt=dateIni, dateFin__lte=dateFin)
        if sn is not None:
            queryset = queryset.filter(sn=sn)

        # Return when no elements are present
        if queryset.count() == 0:
            return Response({"success": True, "data": []})

        # Apply filtering            
        log_allowed = self.get_allowed(request.user, queryset)
        queryset = queryset.filter(id__in=log_allowed)
        if queryset.count() == 0:
            return Response({"success": False, "error": "NOT_ALLOWED"})

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
                    "detectors" : "$detectors"
                    #"id": {  "$toString": "$_id" },
                 
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
            for id in item['detectors']:
                detectors_list.append(str(id))
            item['detectors'] = detectors_list
            data.append(item)
        data = { 
            'success': True,
            'data': data
         } 
        return Response(data)

    def retrieve(self, request, pk=None):
        # Get queryset
        queryset = Log.objects.filter(id=pk)
        if len(queryset) != 1:
            logger.info("Retreived: " + str(len(queryset)))
            return Response({"success": False, "error": "NOT_FOUND"})

        # Apply filtering            
        log_allowed = self.get_allowed(request.user, queryset)
        queryset = queryset.filter(id__in=log_allowed)
        if queryset.count() == 0:
            return Response({"success": False, "error": "NOT_ALLOWED"})

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
                    "detectors" : "$detectors",
                    "route": { "lat": 1, "lon": 1, "aHeight": 1, "fHeight": 1, "time": { "$dateToString": { "format": "%Y-%m-%dT%H:%M:%S:%L", "date": "$dateIni" } }  },
                }
            }
        ]

        # Iterate cursor
        cursor = queryset.aggregate(*pipeline)
        #data = cursor.next()

        data = []
        for item in cursor:
            item['_id'] = str(item['_id'])
            item['id'] = str(item['_id'])
            detectors_list = []
            for id in item['detectors']:
                detectors_list.append(str(id))
            item['detectors'] = detectors_list
            data.append(item)
        data_single = data[0]

        data = { 
            'success': True,
            'data': data_single
        } 
        return Response(data)

    @action(detail=True, methods=['get'],  url_path='kml')
    def kml(self, request, pk = None):

        # Get queryset
        queryset = Log.objects.filter(id=pk)
        if len(queryset) != 1:
            logger.info("Retreived: " + str(len(queryset)))
            return HttpResponse('<xml><success>failed</success><error>NOT_FOUND</error></xml>')

        # Apply filtering            
        log_allowed = self.get_allowed(request.user, queryset)
        queryset = queryset.filter(id__in=log_allowed)
        if queryset.count() == 0:
            return HttpResponse('<xml><success>failed</success><error>NOT_ALLOWED</error></xml>')

        # Route 
        log = queryset.next()
        route_xml = ""
        for route_item in log.route:
            route_xml = route_xml + str(route_item.lat) + ',' + str(route_item.lon) + ',' + str(route_item.fHeight) + ' '        

        # Generate XML
        kml = """<?xml version="1.0" encoding="UTF-8"?>
                    <kml xmlns="http://www.opengis.net/kml/2.2">
                    <Document>
                        <name>{}</name>
                        <description>Trayectoria del Drone</description>
                        <Style id="lineStyle">
                        <LineStyle>
                            <color>7f00ffff</color>
                            <width>4</width>
                        </LineStyle>
                        <PolyStyle>
                            <color>7f00ff00</color>
                        </PolyStyle>
                        </Style>
                        <Placemark>
                        <name>{}</name>
                        <description>Trayectoria del Drone {}</description>
                        <styleUrl>#lineStyle</styleUrl>
                        <LineString>
                            <extrude>1</extrude>
                            <tessellate>1</tessellate>
                            <altitudeMode>relativeToGround</altitudeMode>
                            <coordinates>{}</coordinates>
                        </LineString>
                    </Placemark>
                    </Document>
                    </kml>""".format(pk, pk, pk, route_xml)
        return HttpResponse(kml, content_type='application/xml')


 
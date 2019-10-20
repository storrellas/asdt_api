# Python imports
from datetime import datetime,timedelta



# Django imports
from django.shortcuts import render

# rest framework import
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.permissions import IsAuthenticated

# Project imports
from asdt_api.authentication import ASDTAuthentication

class GetFlight(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def get(self, request):
        data = { 'success': True } 
        return Response(data)

class GetFlightByPage(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def post(self, request):
        print(request.user.data)

        # Get dateIni / dateFin / sn
        query = {
            'dateIni': { '$gt': datetime.now() - timedelta(days=30) },
            'dateIni': { '$lt': datetime.now() },
        }
        if 'dateIni' in request.data:
            dateIni = request.data['dateIni']
        if 'dateFin' in request.data:
            dateFin = request.data['dateIni']
        if 'sn' in request.data:
            sn = request.data['sn']

        data = { 'success - by page': True } 
        return Response(data)

class GetFlightAll(APIView):
    authentication_classes = [ASDTAuthentication]
    permission_classes = (IsAuthenticated,)


    def post(self, request):
        print(request.user.data)
        data = { 'success -all': True } 
        return Response(data)        
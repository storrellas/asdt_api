from django.shortcuts import render
from django.views import View
from django.http import HttpResponse



class Authenticate(View):
    def post(self, request):
        # <view logic>
        return HttpResponse('result')

class UserInfo(View):
    def get(self, request):
        # <view logic>
        return HttpResponse('result')

class AllowedTools(View):
    def get(self, request):
        # <view logic>
        return HttpResponse('result')
import datetime

# Django import - useless
from django.db import models

# Mongoengine imports
from mongoengine import *

# Project imports
from asdt_api.models import ASDTDocument, Location
from user.models import Group

class Model(ASDTDocument):
  meta = {'collection': 'models'}
  
  name = StringField(default='')
  productId = IntField(default=-1)
  image = BooleanField(default=True)
  imageType = StringField(default='')
  imageCode = IntField(default=-1)
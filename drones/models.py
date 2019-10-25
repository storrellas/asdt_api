import datetime

# Django import - useless
from django.db import models

# Mongoengine imports
from mongoengine import *

# Project imports
from asdt_api.models import ASDTDocument, Location
from user.models import Group

class DroneModel(Document):
  meta = {'collection': 'models'}

  name = StringField(default='')
  productId = IntField(default=-1)
  image = BooleanField(default=True)
  imageType = StringField(default='')
  imageCode = IntField(default=-1)

class Drone(ASDTDocument):
  meta = {'collection': 'drones'}
  sn = StringField(required=True, unique=True, default='')
  owner = StringField(required=True, unique=True, default='')
  hide = BooleanField(default=False)
  groups = ListField(ReferenceField(Group, reverse_delete_rule = NULLIFY))
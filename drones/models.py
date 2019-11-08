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
  imageUrl = StringField(default='')
  imageCode = IntField(default=-1)

  def as_dict(self):
    return self.to_mongo().to_dict()

class Drone(ASDTDocument):
  meta = {'collection': 'drones'}
  sn = StringField(required=True, unique=True, default='')
  owner = StringField(required=True, default='')
  hide = BooleanField(default=False)
  groups = ListField(ReferenceField(Group, reverse_delete_rule = NULLIFY))


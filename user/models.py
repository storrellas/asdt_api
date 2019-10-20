# Django import - useless
from django.db import models

from asdt_api.models import ASDTDocument, Location

# Mongoengine imports
from mongoengine import *
import datetime

###############################
# GROUP
###############################

class Inhibitor(ASDTDocument):
  meta = {'collection': 'inhibitors'}
  name = StringField(required=True, unique=True, default='')

class Zone(ASDTDocument):
  meta = {'collection': 'zones'}
  name = StringField(required=True, unique=True, default='')

class Drone(ASDTDocument):
  meta = {'collection': 'drones'}
  sn = StringField(required=True, unique=True, default='')

class GroupDevices(EmbeddedDocument):
  detectors = ListField(LazyReferenceField('Detector'), reverse_delete_rule = NULLIFY)
  inhibitors = ListField(ReferenceField(Inhibitor), reverse_delete_rule = NULLIFY)
  zones = ListField(ReferenceField(Zone), reverse_delete_rule = NULLIFY)
  friendDrones = ListField(ReferenceField(Drone), reverse_delete_rule = NULLIFY)


class Group(ASDTDocument):
  meta = {'collection': 'groups'}

  name = StringField(required=True, unique=True, default='')
  parent = ReferenceField("self", reverse_delete_rule = NULLIFY)
  childs = ListField(ReferenceField("self", reverse_delete_rule = NULLIFY))
  users = ListField(LazyReferenceField('User'), reverse_delete_rule = NULLIFY)  
  devices = EmbeddedDocumentField(GroupDevices)


###############################
# USER
###############################

class CircleZoneCenter(EmbeddedDocument):
  longitude = FloatField(default=0.0)
  latitude = FloatField(default=0.0)

class CircleZone(EmbeddedDocument):
  _id = ObjectIdField()
  center = EmbeddedDocumentField(CircleZoneCenter, default=CircleZoneCenter())
  radius = IntField(default=0)
  color = StringField(default='')
  opacity = StringField(default='')
  id = StringField(default='')
  droneID = ListField(StringField())
  visible = BooleanField(default=False)
  active = BooleanField(default=False)

class DisplayOptions(EmbeddedDocument):
  mapType = StringField(default='')
  zone = ListField(ListField(IntField()))
  circleZone = EmbeddedDocumentListField(CircleZone, default=[])

class User(ASDTDocument):
  meta = {'collection': 'users'}

  email = StringField(required=True, unique=True, default='')
  name = StringField(required=True, default='')
  password = StringField(required=True, default='')
  displayOptions = EmbeddedDocumentField(DisplayOptions, default=DisplayOptions())
  location = EmbeddedDocumentField(Location)
  role = StringField(choices=['MASTER', 'ADMIN', 'EMPOWERED', 'VIEWER'], default='ADMIN')
  hasGroup = BooleanField(default=False)
  group = ReferenceField(Group, reverse_delete_rule = NULLIFY)

  def is_authenticated(self):
    return True
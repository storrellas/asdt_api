# Django import - useless
from django.db import models

from asdt_api.models import ASDTDocument, Location

# Mongoengine imports
from mongoengine import *
import datetime

###############################
# GROUP
###############################

class Group(ASDTDocument):
  meta = {'collection': 'groups'}

  name = StringField(required=True, unique=True, default='')
  parent = ReferenceField("self", reverse_delete_rule = NULLIFY)
  childs = ListField(ReferenceField("self", reverse_delete_rule = NULLIFY))
  users = ListField(LazyReferenceField('Users'), reverse_delete_rule = NULLIFY)


###############################
# DETECTOR
###############################
class DetectorLocation(EmbeddedDocument):
  lat = FloatField(default=41.778443)
  lon = FloatField(default=1.890383)
  height = FloatField(default=10.0)

class Detector(ASDTDocument):
  meta = {'collection': 'detectors'}

  name = StringField(required=True, unique=True, default='')
  password = StringField(required=True, default='')
  location = EmbeddedDocumentField(DetectorLocation)
  groups = ListField(ReferenceField(Group, reverse_delete_rule = NULLIFY))

###############################
# LOGS
###############################

class LogCenterPoint(EmbeddedDocument):
  lat = FloatField(default=0.0)
  lon = FloatField(default=0.0)
  aHeight = FloatField(default=0.0)
  fHeight = FloatField(default=0.0)

class LogRoute(EmbeddedDocument):
  _id = ObjectIdField()
  time = DateTimeField(default=datetime.datetime.now)
  lat = FloatField(default=0.0)
  lon = FloatField(default=0.0)
  aHeight = FloatField(default=0.0)
  fHeight = FloatField(default=0.0)

class LogBoundingBox(EmbeddedDocument):
  maxLat = FloatField(default=0.0)
  maxLon = FloatField(default=0.0)
  minLat = FloatField(default=0.0)
  minLon = FloatField(default=0.0)


class Log(ASDTDocument):
  meta = {'collection': 'logs'}

  # timestamps
  dateIni = DateTimeField(default=datetime.datetime.now)
  dateFin = DateTimeField(default=datetime.datetime.now)
  sn = StringField(default='')

  detectors = ListField(ReferenceField(Detector, reverse_delete_rule = NULLIFY))

  model = StringField(default='')
  productId = IntField(default=-1)
  owner = StringField(default='')

  driverLocation = EmbeddedDocumentField(Location)
  homeLocation = EmbeddedDocumentField(Location)
  maxHeight = FloatField(default=0.0)
  distanceTravelled = FloatField(default=0.0)
  distanceToDetector = FloatField(default=0.0)
  centerPoint = EmbeddedDocumentField(LogCenterPoint, default=LogCenterPoint())
  boundingBox = EmbeddedDocumentField(LogBoundingBox, default=LogCenterPoint())
  route = EmbeddedDocumentListField(LogRoute, default=[])



###############################
# USER
###############################

class CircleZoneCenter(EmbeddedDocument):
  longitude = FloatField()
  latitude = FloatField()

class CircleZone(EmbeddedDocument):
  _id = ObjectIdField()
  center = EmbeddedDocumentField(CircleZoneCenter)
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
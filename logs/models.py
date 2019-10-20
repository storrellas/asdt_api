import datetime

# Django import - useless
from django.db import models



# Mongoengine imports
from mongoengine import *

# Project imports
from asdt_api.models import ASDTDocument, Location
from user.models import Group



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


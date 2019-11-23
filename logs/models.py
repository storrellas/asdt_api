import datetime

# Django import - useless
from django.db import models



# Mongoengine imports
from mongoengine import *

# Project imports
from asdt_api.models import ASDTDocument, Location
from user.models import Group
from detectors.models import Detector


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
  # NOTE: This could be removed and use the createdAt / updatedAt
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
  # NOTE: This is bad spelled
  distanceTraveled = FloatField(default=0.0)
  distanceToDetector = FloatField(default=0.0)
  
  route = EmbeddedDocumentListField(LogRoute, default=[])

  # NOTE: These two are not filled anywhere
  centerPoint = EmbeddedDocumentField(LogCenterPoint, default=LogCenterPoint())
  boundingBox = EmbeddedDocumentField(LogBoundingBox, default=LogBoundingBox())

  def as_dict(self):
    item = {}
    item['_id'] = str(self.id)
    item['dateIni'] = self.dateIni.isoformat()
    item['dateFin'] = self.dateFin.isoformat()
    item['productId'] = self.productId
    item['sn'] = self.sn
    item['model'] = self.model
    item['maxHeight'] = self.maxHeight
    item['distanceTraveled'] = self.distanceTraveled
    item['distanceToDetector'] = self.distanceToDetector
    item['driverLocation'] = {'lat': self.driverLocation.lat, 'lon': self.driverLocation.lon }
    item['homeLocation'] = {'lat': self.homeLocation.lat, 'lon': self.homeLocation.lon }
    detectors_list = []
    for detector in self.detectors:
      detectors_list.append(str(detector.id))
    item['detectors'] = detectors_list
    item['id'] = str(self.id)
    
    return item

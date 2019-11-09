
import datetime

# Django import - useless
from django.db import models



# Mongoengine imports
from mongoengine import *

# Project imports
from asdt_api.models import ASDTDocument, Location
from user.models import Group



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

  def as_dict(self):
    item = {}
    item['id'] = str(self.id)
    item['name'] = self.name  
    item['location'] = {
      'lat': self.location.lat, 
      'lon': self.location.lon,
      'height': self.location.height
    }
    groups_dict = []
    for group in self.groups:
      groups_dict.append(str(group.id))
    item['groups'] = groups_dict
    return item


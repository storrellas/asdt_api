
import datetime
import bcrypt 

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

  __original_password = None

  name = StringField(required=True, unique=True, default='')
  password = StringField(required=True, default='')
  location = EmbeddedDocumentField(DetectorLocation)
  groups = ListField(ReferenceField(Group, reverse_delete_rule = NULLIFY))

  def set_password(self, password):
    self.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10)).decode()
    self.__original_password = self.password
    return self.save()

  def save(self, *args, **kwargs):
    # Update password
    if self.password != self.__original_password:
      self.password = bcrypt.hashpw(self.password.encode(), bcrypt.gensalt(10)).decode()
      self.__original_password = self.password
    return super().save(*args, **kwargs)


  def as_dict(self):
    item = {}
    item['id'] = str(self.id)
    item['name'] = self.name
    if self.location is not None:  
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


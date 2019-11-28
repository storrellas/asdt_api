import datetime

# Django import - useless
from django.db import models



# Mongoengine imports
from mongoengine import *

# Project imports
from asdt_api.models import ASDTDocument, Location
from user.models import Group


###############################
# ZONE
###############################

class Zone(ASDTDocument):
  meta = {'collection': 'zones'}
  name = StringField(required=True, unique=True, default='')
  center = EmbeddedDocumentField(Location)
  radius = IntField()
  perimiter = ListField(EmbeddedDocumentField(Location))
  maxLat = IntField()
  maxLon = IntField()
  minLat = IntField()
  minLon = IntField()
  # NOTE: This property is not used anymore
  # Leave it here for compatiblity with old DB's
  # Currently, making use of group.devices references
  groups = ListField(ReferenceField(Group, reverse_delete_rule = NULLIFY))

  def as_dict(self):
    item = {}
    item['id'] = str(self.id)
    item['name'] = self.name
    if self.center is not None: 
      item['center'] = { 'lat': self.center.lat, 'lon': self.center.lon}
    else:
      item['center'] = { 'lat': 0, 'lon': 0}
    item['radius'] = self.radius
    perimeter_dict = []
    for permiter in self.perimiter:      
      perimeter_dict.append({ 'lat': permiter.lat, 'lon': permiter.lon})
    item['perimeter'] = perimeter_dict      
    groups_dict = []
    for group in self.groups:
      groups_dict.append(str(group.id))
    item['groups'] = groups_dict
    return item
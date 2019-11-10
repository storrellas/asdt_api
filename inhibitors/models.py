import datetime

# Django import - useless
from django.db import models



# Mongoengine imports
from mongoengine import *

# Project imports
from asdt_api.models import ASDTDocument, Location
from user.models import Group


class Inhibitor(ASDTDocument):
  meta = {'collection': 'inhibitors'}
  name = StringField(required=True, unique=True, default='')
  password = StringField(required=True, default='')
  location = EmbeddedDocumentField(Location)
  frequencies = ListField(StringField(required=True, default=''))
  groups = ListField(ReferenceField(Group, reverse_delete_rule = NULLIFY))

  def as_dict(self):
    item = {}
    item['id'] = str(self.id)
    item['name'] = self.name
    if self.location is not None:    
      item['location'] = { 'lat': self.location.lat, 'lon': self.location.lon}
    item['frequencies'] = self.frequencies
    groups_dict = []
    for group in self.groups:
      groups_dict.append(str(group.id))
    item['groups'] = groups_dict
    return item
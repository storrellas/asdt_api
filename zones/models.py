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
  groups = ListField(ReferenceField(Group, reverse_delete_rule = NULLIFY))
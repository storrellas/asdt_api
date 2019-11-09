
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

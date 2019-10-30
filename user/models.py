import bcrypt 

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



class GroupDevices(EmbeddedDocument):
  detectors = ListField(LazyReferenceField('Detector'), reverse_delete_rule = NULLIFY)
  inhibitors = ListField(ReferenceField(Inhibitor), reverse_delete_rule = NULLIFY)
  zones = ListField(ReferenceField(Zone), reverse_delete_rule = NULLIFY)
  friendDrones = ListField(LazyReferenceField('Drone'), reverse_delete_rule = NULLIFY)


class Group(ASDTDocument):
  meta = {'collection': 'groups'}

  name = StringField(required=True, unique=True, default='')
  parent = ReferenceField("self", reverse_delete_rule = NULLIFY)
  childs = ListField(ReferenceField("self", reverse_delete_rule = NULLIFY))
  users = ListField(LazyReferenceField('User'), reverse_delete_rule = NULLIFY)  
  devices = EmbeddedDocumentField(GroupDevices, default=GroupDevices())

  def get_devices(self):
    devices = self.devices
    for child_group in self.childs:
      
      child_group.devices = child_group.get_devices()
      if child_group.devices.detectors is not None:
        devices.detectors.extend(child_group.devices.detectors)
      
      if child_group.devices.inhibitors is not None:
        devices.detectors.extend(child_group.devices.inhibitors)

      if child_group.devices.zones is not None:
        devices.detectors.extend(child_group.devices.zones)

      if child_group.devices.friendDrones is not None:
        devices.detectors.extend(child_group.devices.friendDrones)
    
    return devices



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
  
  __original_password = None

  email = StringField(required=True, unique=True, default='')
  name = StringField(required=True, default='')
  password = StringField(required=True, default='')
  displayOptions = EmbeddedDocumentField(DisplayOptions, default=DisplayOptions())
  location = EmbeddedDocumentField(Location)
  role = StringField(choices=['MASTER', 'ADMIN', 'EMPOWERED', 'VIEWER'], default='ADMIN')
  hasGroup = BooleanField(default=False)
  group = ReferenceField(Group, reverse_delete_rule = NULLIFY)
  concrete_model = None

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.__original_password = self.password

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


  def is_authenticated(self):
    return True
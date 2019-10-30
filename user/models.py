import bcrypt 

# Django import - useless
from django.db import models

from asdt_api.models import ASDTDocument, Location


# Mongoengine imports
from mongoengine import *
import datetime

from asdt_api.utils import get_logger
from groups.models import Group

logger = get_logger()




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
  
  def has_power_over(self, user):
    if self.hasGroup == False or \
        self.group is None or \
        self.role != 'ADMIN':
      return False

    # User does not have group and user is root of site (self.group.parent == None)
    if user.group is None:
      return True if self.group.parent is None else False

    # If both self and user share group
    if user.group == self.group:
      # Return True when user is not admin
      return True if user.role != 'ADMIN' else False
    else:
      # Return True when current group is parent of user group
      return self.group.is_parent_of(user.group)


    
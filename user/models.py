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

  MASTER = 'MASTER'
  ADMIN = 'ADMIN'
  EMPOWERED = 'EMPOWERED'
  VIEWER = 'VIEWER'
  role_list = [MASTER, ADMIN, EMPOWERED, VIEWER]


  email = StringField(required=True, unique=True, default='')
  name = StringField(required=True, default='')
  password = StringField(required=True, default='')
  displayOptions = EmbeddedDocumentField(DisplayOptions, default=DisplayOptions())
  location = EmbeddedDocumentField(Location)
  role = StringField(choices=role_list, default=ADMIN)
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
    # If MASTER
    if self.role == User.MASTER:
      return True

    # If ADMIN
    if self.role == User.ADMIN and self.group is not None:
      if user.group == self.group or self.group.is_parent_of(user.group):
        return True

    return False

    # if self.hasGroup == False or \
    #     self.group is None or \
    #     self.role != User.ADMIN:
    #   return False

    # # User does not have group and user is root of site (self.group.parent == None)
    # if user.group is None:
    #   return True if self.group.parent is None else False

    # # If both self and user share group
    # if user.group == self.group:
    #   # Return True when user is not admin
    #   return True if user.role != User.ADMIN else False
    # else:
    #   # Return True when current group is parent of user group
    #   return self.group.is_parent_of(user.group)

  def is_allowed_group(self, group):
    # If MASTER
    if self.role == self.MASTER:
      return True

    # If ADMIN
    if self.role == self.ADMIN:
      return  (self.group == group or self.group.is_parent_of(group) )
    
    return False

  def as_dict(self):
    item = {}
    item['id'] = str(self.id)
    item['name'] = self.name
    item['email'] = self.email
    item['role'] = self.role
    item['createdAt'] = self.createdAt.isoformat()
    item['updatedAt'] = self.updatedAt.isoformat()
    item['hasGroup'] = self.hasGroup    
    item['group'] = str(self.group.id) if self.group is not None else None   
    zone_dict = []
    for zone in self.displayOptions.zone:
      zone_dict.append(zone)
    cicleZone_dict = []      
    for circleZone in self.displayOptions.circleZone:
      cicleZone_dict.append({
        'id': str(circleZone.id), 
        'center': {'latitude':circleZone.center.latitude, 'longitude':circleZone.center.longitude},
        'radius': circleZone.radius, 'color': circleZone.color,
        'opacity': circleZone.opacity, 'droneID': circleZone.droneID,
        'visible': circleZone.visible, 'active': circleZone.active
      })
    item['displayOptions'] = { 'zone': zone_dict, 'circleZone': cicleZone_dict }

    return item
    
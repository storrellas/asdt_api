from django.db import models

from asdt_api.models import ASDTDocument, Location


# Mongoengine imports
from mongoengine import *
import datetime

from asdt_api.utils import get_logger

logger = get_logger()

class Inhibitor(ASDTDocument):
  meta = {'collection': 'inhibitors'}
  name = StringField(required=True, unique=True, default='')

class Zone(ASDTDocument):
  meta = {'collection': 'zones'}
  name = StringField(required=True, unique=True, default='')

###############################
# GROUP
###############################


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

  def get_full_devices(self):
    """
    Returns a list of all devices within child groups
    """
    devices = self.devices
    for child_group in self.childs:

      child_group.devices = child_group.get_full_devices()
      if child_group.devices.detectors is not None:
        devices.detectors.extend(child_group.devices.detectors)
      
      if child_group.devices.inhibitors is not None:
        devices.detectors.extend(child_group.devices.inhibitors)

      if child_group.devices.zones is not None:
        devices.detectors.extend(child_group.devices.zones)

      if child_group.devices.friendDrones is not None:
        devices.detectors.extend(child_group.devices.friendDrones)
    
    return devices

  def get_full_children(self):
    """
    Returns a list of all devices within child groups
    """
    children = self.childs      
    for child_group in self.childs:
      children.extend( child_group.get_full_children() )

    return children

  def is_parent_of(self, group):
    """
    Checks whether 'group' indicated is parent of self
    """    
    tmp = group
    while tmp.parent is not None: 
      try:       
        tmp = self._qs.get(id=tmp.parent.id)
        if tmp.id == self.id:
          return True
      except Exception as e:
        print(e)
        logger.info("parent not found {}".format(tmp.parent.id))
        return False  
    return False

  def remove_user(self, user_target):
    """
    Removes user from group
    """
    self.users.remove(user_target)
    self.save()

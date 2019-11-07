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

  def get_tree_children(self):
    """
    Returns a tree with all children
    """
    children = []
    for child_group in self.childs:
      children.append( child_group.get_tree_children() )
    return {'id': str(self.id), 'children': children }
    #return {'id': str(self.name), 'children': children }

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

  def as_dict(self):
    item = {}
    item['id'] = str(group.id)
    item['name'] = str(group.name)
    item['parent'] = str(group.parent.id) if group.parent is not None else 'undef'
    item['users'] = []
    for user in group.users:
      item['users'].append(str(user.id))
    item['childs'] = []
    for group_child in group.childs:
      item['childs'].append(str(group_child.id))
    
    detectors_list = []
    for detector in group.devices.detectors:
      detectors_list.append( str(detector.id) )
    inhibitor_list = []
    for inhibitor in group.devices.inhibitors:
      inhibitor_list.append( str(inhibitor.id) )
    zones_list = []
    for zone in group.devices.zones:
      zones_list.append( str(zone.id) )
    friend_drone_list = []
    for friend_drone in group.devices.friendDrones:
      friend_drone_list.append( str(friend_drone.id) )
    item['devices'] = {
      'detectors' : detectors_list,
      'inhibitors' : inhibitor_list,
      'zones' : zones_list,
      'friendDrones' : friend_drone_list,
    }
    return item
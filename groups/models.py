import importlib

from django.db import models

from asdt_api.models import ASDTDocument, Location


# Mongoengine imports
from mongoengine import *
from bson.objectid import ObjectId
import datetime

from asdt_api.utils import get_logger
from asdt_api.models import Location

logger = get_logger()

# Dynamically import modules
inhibitors = importlib.import_module('inhibitors')
detectors = importlib.import_module('detectors')
zones = importlib.import_module('zones')
drones = importlib.import_module('drones')
user = importlib.import_module('user')

###############################
# GROUP
###############################

class GroupDevices(EmbeddedDocument):
  detectors = ListField(LazyReferenceField('Detector'))
  inhibitors = ListField(LazyReferenceField('Inhibitor'))
  zones = ListField(LazyReferenceField('Zone'))
  friendDrones = ListField(LazyReferenceField('Drone'))


class Group(ASDTDocument):
  meta = {'collection': 'groups'}

  name = StringField(required=True, unique=True, default='')
  parent = ReferenceField("self", reverse_delete_rule = NULLIFY)
  childs = ListField(ReferenceField("self", reverse_delete_rule = NULLIFY))
  # NOTE: This property is not used anymore
  # Leave it here for compatiblity with old DB's
  # Currently, making use of User.parent references
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
        devices.inhibitors.extend(child_group.devices.inhibitors)

      if child_group.devices.zones is not None:
        devices.zones.extend(child_group.devices.zones)

      if child_group.devices.friendDrones is not None:
        devices.friendDrones.extend(child_group.devices.friendDrones)
    
    return devices

  def get_tree_children(self):
    """
    Returns a tree with all children
    """
    children = []
    for child_group in self.childs:
      children.append( child_group.get_tree_children() )
    return {'id': str(self.id), 'children': children }

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


  def delete_recursive(self):
    """
    Removes references for users / devices
    """
    for child in self.childs:
      child.delete_recursive()
    self.delete()

  def append_device(self, instance):
    """
    Appends item from list
    """

    if isinstance(instance, inhibitors.models.Inhibitor):
      self.devices.inhibitors.append(instance)

    if isinstance(instance, detectors.models.Detector):
      self.devices.detectors.append(instance)
    
    if isinstance(instance, zones.models.Zone):
      self.devices.zones.append(instance)

    if isinstance(instance, drones.models.Drone):
      self.devices.friendDrones.append(instance)

    self.save()

  def remove_device(self, instance):
    """
    Removes item from list
    """

    if isinstance(instance, inhibitors.models.Inhibitor):
      self.devices.inhibitors.remove(instance)

    if isinstance(instance, detectors.models.Detector):
      self.devices.detectors.remove(instance)
    
    if isinstance(instance, zones.models.Zone):
      self.devices.zones.remove(instance)

    if isinstance(instance, drones.models.Drone):
      self.devices.friendDrones.remove(instance)
    self.save()

  def has_device(self, instance):
    """
    Check whether device is in list
    """

    if isinstance(instance, inhibitors.models.Inhibitor):
      return True if instance in self.devices.inhibitors else False

    if isinstance(instance, detectors.models.Detector):
      return True if instance in self.devices.detectors else False
    
    if isinstance(instance, zones.models.Zone):
      return True if instance in self.devices.zones else False

    if isinstance(instance, drones.models.Drone):
      return True if instance in self.devices.friendDrones else False


  def as_dict(self):
    item = {}
    item['id'] = str(self.id)
    item['name'] = str(self.name)
    item['parent'] = str(self.parent.id) if self.parent is not None else 'undef'
    item['users'] = []
    for user_item in user.models.User.objects.filter(group=self.id):
      item['users'].append(user_item.as_dict())
    item['childs'] = []
    for group_child in self.childs:
      item['childs'].append(str(group_child.id))
    
    detectors_list = []
    for detector in self.devices.detectors:
      detectors_list.append( str(detector.id) )
    inhibitor_list = []
    for inhibitor in self.devices.inhibitors:
      inhibitor_list.append( str(inhibitor.id) )
    zones_list = []
    for zone in self.devices.zones:
      zones_list.append( str(zone.id) )
    friend_drone_list = []
    for friend_drone in self.devices.friendDrones:
      friend_drone_list.append( str(friend_drone.id) )
    item['devices'] = {
      'detectors' : detectors_list,
      'inhibitors' : inhibitor_list,
      'zones' : zones_list,
      'friendDrones' : friend_drone_list,
    }
    return item
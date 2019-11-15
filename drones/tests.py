import json
from http import HTTPStatus

# Django imports
from django.test import TestCase, Client
from django.http import HttpRequest
from django.conf import settings
from rest_framework.test import APITestCase
from unittest.mock import patch

# Projet imports
from asdt_api import utils
from asdt_api import helper_tests
from mongo_dummy import MongoDummy
from .models import *

logger = utils.get_logger()

class TestCase(helper_tests.DeviceTestCase):

  base_url = '/{}/drones/'.format(settings.PREFIX)
  model = Drone

  @classmethod
  def setUpClass(cls):
    """
    Called once in every suite
    """
    super().setUpClass()

  def setUp(self):
    """
    Called before every test
    """
    super().setUp()

  def test_list(self):
    super().test_list()

  def test_retrieve(self):    
    # Retrieve detector
    instance = Drone.objects.get(sn='1')
    super().test_retrieve(instance.id)

  def test_get_model(self):
    # Get token
    self.authenticate('admin@asdt.eu', 'asdt2019')

    # Get Model
    response = self.client.get('/{}/drones/model/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(len(response_json['data']) > 0)

  def test_create_update_delete(self):

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_updated = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Create
    body = {
      'sn' : 'mysn',
      'owner': 'myowner',
      'hide' : True,
      'groups': [ str(group.id) ]
    }

    # Update
    bodyupdated = {
      'sn' : 'mysnupdated',
      'owner': 'myowner',
      'hide' : True,
      'groups': [ str(group_updated.id) ]
    }
    super().test_create_update_delete(body, bodyupdated)

    """
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Create
    body = {
      'sn' : 'mysn',
      'owner': 'myowner',
      'hide' : True,
      'groups': [ str(group.id) ]
    }
    response = self.client.post('/{}/drones/'.format(settings.PREFIX), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Check properly created
    drone = Drone.objects.get(sn='mysn')
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertTrue( drone in group.devices.friendDrones )
    self.assertTrue( group in drone.groups )


    # Update
    body = {
      'sn' : 'mysnupdated',
      'owner': 'myowner',
      'hide' : True,
      'groups': [ str(group_2.id) ]
    }
    response = self.client.put('/{}/drones/{}/'.format(settings.PREFIX, drone.id), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    

    # Check properly created
    drone = Drone.objects.get( sn='mysnupdated' )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertFalse( drone in group.devices.friendDrones )
    self.assertTrue( drone in group2.devices.friendDrones )
    self.assertTrue( group2 in drone.groups )

    # Delete
    response = self.client.delete('/{}/drones/{}/'.format(settings.PREFIX, drone.id), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT) 

    # Check properly created    
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertTrue( Drone.objects.filter( sn='mysnupdated' ).count() == 0 )
    """

  def test_update_only_group(self):

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_updated = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Create
    body = {
      'sn' : 'mysn',
      'owner': 'myowner',
      'hide' : True,
      'groups': [ str(group.id) ]
    }

    # Update
    bodyupdated = {
      'groups': [ str(group_updated.id) ]
    }
    super().test_update_only_group(body, bodyupdated)

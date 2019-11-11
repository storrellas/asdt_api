from django.test import TestCase

# Create your tests here.
import csv, json
from http import HTTPStatus

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
from user.models import User

logger = utils.get_logger()


class TestCase(helper_tests.DeviceTestCase):

  base_url = '/{}/zones/'.format(settings.PREFIX)

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
    instance = Zone.objects.get(name='zone1')
    super().test_retrieve(instance.id)


  def test_create_update_delete(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Create
    body = {
      'name' : 'myname',
      'center' : {'lat': 12.3, 'lon': 3.2 },
      'radius' : 2,
      'perimiter' : [{'lat': 12.3, 'lon': 3.2 }],
      'maxLat' : 2,
      'maxLon' : 2,
      'minLat' : 2,
      'minLon' : 2,
      'groups': [ str(group.id) ]
    }
    response = self.client.post('/{}/zones/'.format(settings.PREFIX), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check properly created
    zone = Zone.objects.get( name='myname' )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertTrue( zone in group.devices.zones )
    self.assertTrue( group in zone.groups )


    # Update
    body = {
      'name' : 'mynameupdated',
      'center' : {'lat': 12.3, 'lon': 3.2 },
      'radius' : 2,
      'perimiter' : [{'lat': 12.3, 'lon': 3.2 }],
      'maxLat' : 2,
      'maxLon' : 2,
      'minLat' : 2,
      'minLon' : 2,
      'groups': [ str(group_2.id) ]
    }
    response = self.client.put('/{}/zones/{}/'.format(settings.PREFIX, zone.id), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check properly created
    zone = Zone.objects.get( name='mynameupdated' )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertFalse( zone in group.devices.zones )
    self.assertTrue( zone in group2.devices.zones )
    self.assertTrue( group2 in zone.groups )

    # Delete
    response = self.client.delete('/{}/zones/{}/'.format(settings.PREFIX, zone.id), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check properly created    
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertTrue( Zone.objects.filter( name='mynameupdated' ).count() == 0 )

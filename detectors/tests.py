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

  base_url = '/{}/detectors/'.format(settings.PREFIX)

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
    instance = Detector.objects.get(name='detector2')
    super().test_retrieve(instance.id)


  def test_retrieve_not_allowed(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Retrieve detector
    detector = Detector.objects.get(name='detector1')

    # Get single
    response = self.client.get('/{}/detectors/{}/'.format(settings.PREFIX, detector.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertFalse(response_json['success'])

  def test_create_update_delete(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Create
    body = {
      'name' : 'myname',
      'password': 'mypassword',
      'location' : {'lat': 12.3, 'lon': 3.2, 'height': 5.4 },
      'groups': [ str(group.id) ]
    }
    response = self.client.post('/{}/detectors/'.format(settings.PREFIX), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check properly created
    detector = Detector.objects.get( name='myname' )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertTrue( detector in group.devices.detectors )
    self.assertTrue( group in detector.groups )


    # Update
    body = {
      'name' : 'mynameupdated',
      'password': 'mypassword',
      'location' : {'lat': 12.3, 'lon': 3.2, 'height': 5.4 },
      'groups': [ str(group_2.id) ]
    }
    response = self.client.put('/{}/detectors/{}/'.format(settings.PREFIX, detector.id), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check properly created
    detector = Detector.objects.get( name='mynameupdated' )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertFalse( detector in group.devices.detectors )
    self.assertTrue( detector in group2.devices.detectors )
    self.assertTrue( group2 in detector.groups )

    # Delete
    response = self.client.delete('/{}/detectors/{}/'.format(settings.PREFIX, detector.id), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check properly created    
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertTrue( Detector.objects.filter( name='mynameupdated' ).count() == 0 )


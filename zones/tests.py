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
from mongo_dummy import MongoDummy
from .models import *
from user.models import User

logger = utils.get_logger()

class TestCase(APITestCase):


  @classmethod
  def setUpClass(cls):
    """
    Called once in every suite
    """
    super().setUpClass()
    logger.info("----------------------------")
    logger.info("--- Generating scenario  ---")
    logger.info("----------------------------")    
    settings.MONGO_DB = 'asdt_test'
    logger.info("DB Generated: {}".format(settings.MONGO_DB))

    mongo_dummy = MongoDummy()
    mongo_dummy.setup(settings.MONGO_DB, settings.MONGO_HOST, int(settings.MONGO_PORT))
    mongo_dummy.generate_scenario()

  def setUp(self):
    """
    Called before every test
    """
    pass

  def authenticate(self, user, password):
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                            { "email": user, "password": password })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)


  def test_list(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get All
    response = self.client.get('/api/v2/zones/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

  def test_retrieve(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Retrieve detector
    zone = Zone.objects.get(name='zone1')

    # Get single
    response = self.client.get('/api/v2/zones/{}/'.format(zone.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

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
    response = self.client.post('/api/v2/zones/', body, format='json')
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
    response = self.client.put('/api/v2/zones/{}/'.format(zone.id), body, format='json')
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
    response = self.client.delete('/api/v2/zones/{}/'.format(zone.id), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check properly created    
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertTrue( Zone.objects.filter( name='mynameupdated' ).count() == 0 )

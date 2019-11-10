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
from mongo_dummy import MongoDummy
from .models import *

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


  def test_get_model(self):
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Get Model
    response = self.client.get('/api/v2/drones/model/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(len(response_json['data']) > 0)

  def test_list(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get All
    response = self.client.get('/api/v2/drones/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

  def test_retrieve(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Retrieve detector
    drone = Drone.objects.get(sn='1')

    # Get single
    response = self.client.get('/api/v2/drones/{}/'.format(drone.id))
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
      'sn' : 'mysn',
      'owner': 'myowner',
      'hide' : True,
      'groups': [ str(group.id) ]
    }
    response = self.client.post('/api/v2/drones/', body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check properly created
    drone = Drone.objects.get( sn='mysn' )
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
    response = self.client.put('/api/v2/drones/{}/'.format(drone.id), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check properly created
    drone = Drone.objects.get( sn='mysnupdated' )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertFalse( drone in group.devices.friendDrones )
    self.assertTrue( drone in group2.devices.friendDrones )
    self.assertTrue( group2 in drone.groups )

    # Delete
    response = self.client.delete('/api/v2/drones/{}/'.format(drone.id), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check properly created    
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertTrue( Drone.objects.filter( sn='mysnupdated' ).count() == 0 )

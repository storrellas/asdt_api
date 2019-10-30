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

logger = utils.get_logger()

class UserTestCase(APITestCase):


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


  def test_group_get_full_devices(self):
    group = Group.objects.get(name='ADMIN_ASDT')
    devices = group.get_full_devices()
    self.assertTrue(len(devices.detectors) == 3)
    

  def test_group_is_parent_of(self):
    # Check Ok
    admin_child_child_group = Group.objects.get(name='ADMIN_CHILD_CHILD_ASDT')
    admin_group = Group.objects.get(name='ADMIN_ASDT')
    self.assertTrue(admin_group.is_parent_of(admin_child_child_group))

    # Check inverse    
    self.assertFalse(admin_child_child_group.is_parent_of(admin_group))

    # Check other group
    viewer_group = Group.objects.get(name='VIEWER_ASDT')
    self.assertFalse(admin_group.is_parent_of(viewer_group))


  def test_get_token_admin(self):
    
    # Check not workin without login
    response = self.client.get('/api/v2/user/me/')
    self.assertTrue(response.status_code == HTTPStatus.FORBIDDEN)

    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Check user info
    response = self.client.get('/api/v2/user/me/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['data']['email'], 'admin@asdt.eu')

    # Check tools
    response = self.client.get('/api/v2/user/me/tools/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['data']['SETTING'], True)


  def test_get_token_viewer(self):
    
    # Check not workin without login
    response = self.client.get('/api/v2/user/me/')
    self.assertTrue(response.status_code == HTTPStatus.FORBIDDEN)

    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "viewer@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Check user info
    response = self.client.get('/api/v2/user/me/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['data']['email'], 'viewer@asdt.eu')

    # Check tools
    response = self.client.get('/api/v2/user/me/tools/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['data']['SETTING'], False)

  def test_create_user(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Check not workin without login
    body = {
      "email": "user@test.eu",
      "password": "asdt2019",
      "name": "Oussama",
      "role": "EMPOWERED",
      "hasGroup": False
    }
    response = self.client.post('/api/v2/user/', body)
    self.assertTrue(response_json['success'] == True)

    # Get token
    self.client.credentials(HTTP_AUTHORIZATION='')
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "user@test.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'] == True)

  def test_create_user_group(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Add user to group
    group = Group.objects.first()

    # Check not workin without login
    body = {
      "email": "user2@test.eu",
      "password": "asdt2019",
      "name": "Oussama",
      "role": "EMPOWERED",
      "hasGroup": True,
      "group": group.id
    }
    response = self.client.post('/api/v2/user/', body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['data']['group'] == str(group.id))

    # Get token
    self.client.credentials(HTTP_AUTHORIZATION='')
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "user2@test.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())



  def test_create_user_forbidden(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "viewer@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Check not workin without login
    body = {
      "email": "user@test.com",
      "password": "asdt2019",
      "name": "Oussama",
      "role": "EMPOWERED",
      "hasGroup": False
    }
    response = self.client.post('/api/v2/user/', body)
    self.assertTrue(response.status_code == HTTPStatus.FORBIDDEN)






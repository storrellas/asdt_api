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
    self.assertTrue(response_json['success'])

    # Get token
    self.client.credentials(HTTP_AUTHORIZATION='')
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "user@test.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Delete created user
    User.objects.filter(email='user@test.eu').delete()

  def test_create_user_group(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Add user to group
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')

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
    self.assertTrue(response_json['success'])
    self.assertTrue(response_json['data']['group'] == str(group.id))

    # Get token
    self.client.credentials(HTTP_AUTHORIZATION='')
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "user2@test.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())

    # # Delete created user
    # User.objects.filter(email='user2@test.eu').delete()
    # Delete user
    user = User.objects.get(email='user2@test.eu')
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group.remove_user(user)
    user.delete()


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

  def test_create_user_group_not_allowed(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Add user to group
    group = Group.objects.get(name='VIEWER_ASDT')

    # Check not workin without login
    body = {
      "email": "user@test.com",
      "password": "asdt2019",
      "name": "Oussama",
      "role": "EMPOWERED",
      "hasGroup": True,
      "group": group.id
    }
    response = self.client.post('/api/v2/user/', body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertFalse(response_json['success'])


  def test_list_admin(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Get list of users
    response = self.client.get('/api/v2/user/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertTrue(len(response_json['data']) == 7)

  def test_list_admin_child(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin_child@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Get list of users
    response = self.client.get('/api/v2/user/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertTrue(len(response_json['data']) == 2)

  def test_retreive(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    user = User.objects.get(email='admin_child@asdt.eu')

    # Get list of users
    response = self.client.get('/api/v2/user/{}/'.format(user.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])


  def test_update(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    user = User.objects.get(email='admin_child@asdt.eu')

    # Update user
    body = {
      "name": "Albert",
    }
    response = self.client.put('/api/v2/user/{}/'.format(user.id), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertTrue(response_json['data']['name'] == 'Albert')

  def test_delete(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Create custom user    
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    user = User.objects.create(email='test_delete@asdt.eu', hasGroup=True, group=group)
    
    # Add user to group
    group.users.append(user)
    group.save()

    # Delete user
    response = self.client.delete('/api/v2/user/{}/'.format(user.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertTrue( User.objects.filter(email='test_delete@asdt.eu').count() == 0 )

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertTrue(len(group.users) == 1)






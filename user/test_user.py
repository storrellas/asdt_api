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
    response = self.client.post('/{}/user/authenticate/'.format(settings.PREFIX), 
                            { "email": user, "password": password })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

  def test_get_token_admin(self):
    
    # Check not workin without login
    response = self.client.get('/{}/user/me/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.FORBIDDEN)

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Check user info
    response = self.client.get('/{}/user/me/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['data']['email'], 'admin@asdt.eu')

    # Check tools
    response = self.client.get('/{}/user/me/tools/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['data']['SETTING'], True)


  def test_get_token_viewer(self):
    
    # Check not workin without login
    response = self.client.get('/{}/user/me/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.FORBIDDEN)

    # Get Token
    self.authenticate("viewer@asdt.eu", "asdt2019")

    # Check user info
    response = self.client.get('/{}/user/me/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['data']['email'], 'viewer@asdt.eu')
    self.assertTrue(response_json['success'])

    # Check tools
    response = self.client.get('/{}/user/me/tools/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['data']['SETTING'], False)
    self.assertTrue(response_json['success'])

  def test_create_user(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Check not workin without login
    body = {
      "email": "user@test.eu",
      "password": "asdt2019",
      "name": "Oussama",
      "role": "EMPOWERED",
      "hasGroup": False
    }
    response = self.client.post('/{}/user/'.format(settings.PREFIX), body)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Get token
    self.client.credentials(HTTP_AUTHORIZATION='')
    response = self.client.post('/{}/user/authenticate/'.format(settings.PREFIX), 
                                { "email": "user@test.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Delete created user
    User.objects.filter(email='user@test.eu').delete()

  def test_create_user_group(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

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
    response = self.client.post('/{}/user/'.format(settings.PREFIX), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertTrue(response_json['data']['group'] == str(group.id))

    # Get token
    self.client.credentials(HTTP_AUTHORIZATION='')
    response = self.client.post('/{}/user/authenticate/'.format(settings.PREFIX), 
                                { "email": "user2@test.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Delete user
    user = User.objects.get(email='user2@test.eu')
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')    
    group.users.remove(user)
    group.save()

    # Delete user
    user.delete()


  def test_create_user_forbidden(self):
    
    # Get Token
    self.authenticate("viewer@asdt.eu", "asdt2019")

    # Check not workin without login
    body = {
      "email": "user@test.com",
      "password": "asdt2019",
      "name": "Oussama",
      "role": "EMPOWERED",
      "hasGroup": False
    }
    response = self.client.post('/{}/user/'.format(settings.PREFIX), body)
    self.assertTrue(response.status_code == HTTPStatus.FORBIDDEN)

  def test_create_user_group_not_allowed(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

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
    response = self.client.post('/{}/user/'.format(settings.PREFIX), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertFalse(response_json['success'])


  def test_list_admin(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get list of users
    response = self.client.get('/{}/user/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertEqual(len(response_json['data']), 7)

  def test_list_admin_child(self):
    
    # Get Token
    self.authenticate("admin_child@asdt.eu", "asdt2019")

    # Get list of users
    response = self.client.get('/{}/user/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertEqual(len(response_json['data']), 2)

  def test_retreive(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    user = User.objects.get(email='admin_child@asdt.eu')

    # Get list of users
    response = self.client.get('/{}/user/{}/'.format(settings.PREFIX, user.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])


  # def test_update(self):
    
  #   # Get Token
  #   self.authenticate("admin@asdt.eu", "asdt2019")

  #   user = User.objects.get(email='admin_child@asdt.eu')

  #   # Update user
  #   body = {
  #     "name": "Albert",
  #   }
  #   response = self.client.put('/{}/user/{}/'.format(settings.PREFIX, user.id), body)
  #   self.assertTrue(response.status_code == HTTPStatus.OK)
  #   response_json = json.loads(response.content.decode())
  #   self.assertTrue(response_json['success'])
  #   self.assertTrue(response_json['data']['name'] == 'Albert')

  def test_delete(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Create custom user    
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    user = User.objects.create(email='test_delete@asdt.eu', hasGroup=True, group=group)
    
    # Add user to group
    group.users.append(user)
    group.save()

    # Delete user
    response = self.client.delete('/{}/user/{}/'.format(settings.PREFIX, user.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertTrue( User.objects.filter(email='test_delete@asdt.eu').count() == 0 )

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertTrue(len(group.users), 1)






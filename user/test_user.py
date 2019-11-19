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

logger = utils.get_logger()

class TestCase(helper_tests.ASDTTestCase):


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
    pass

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
    self.assertEqual(response_json['email'], 'admin@asdt.eu')

    # Check tools
    response = self.client.get('/{}/user/me/tools/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['SETTING'], True)


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
    self.assertEqual(response_json['email'], 'viewer@asdt.eu')

    # Check tools
    response = self.client.get('/{}/user/me/tools/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['SETTING'], False)

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

    # Get token
    self.client.credentials(HTTP_AUTHORIZATION='')
    response = self.client.post('/{}/user/authenticate/'.format(settings.PREFIX), 
                                { "email": "user@test.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)

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
    self.assertTrue(response_json['group'] == str(group.id))

    # Get token
    self.client.credentials(HTTP_AUTHORIZATION='')
    response = self.client.post('/{}/user/authenticate/'.format(settings.PREFIX), 
                                { "email": "user2@test.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Delete user
    user = User.objects.get(email='user2@test.eu')

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
    self.assertTrue(response.status_code == HTTPStatus.BAD_REQUEST)

  def test_list_admin(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get list of users
    response = self.client.get('/{}/user/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(len(response_json), 3)

  def test_list_master(self):
    
    # Get Token
    self.authenticate("master@asdt.eu", "asdt2019")

    # Get list of users
    response = self.client.get('/{}/user/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(len(response_json), 7)

  def test_list_admin_child(self):
    
    # Get Token
    self.authenticate("admin_child@asdt.eu", "asdt2019")

    # Get list of users
    response = self.client.get('/{}/user/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(len(response_json), 2)

  def test_retreive(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    user = User.objects.get(email='admin_child@asdt.eu')

    # Get list of users
    response = self.client.get('/{}/user/{}/'.format(settings.PREFIX, user.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)

  def test_update(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")


    # Create custom user    
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_former = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    user = User.objects.create(email='sergi@asdt.eu', name='Sergi', group=group_former)
    user.set_password('asdt2019')
    
    # Update user
    body = {
      "email": "albert@asdt.eu",
      "password": "asdt2018",
      "group": str(group.id)
    }
    response = self.client.put('/{}/user/{}/'.format(settings.PREFIX, user.id), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['email'] == 'albert@asdt.eu')

    # Get token
    self.client.credentials(HTTP_AUTHORIZATION='')
    response = self.client.post('/{}/user/authenticate/'.format(settings.PREFIX), 
                                { "email": "albert@asdt.eu", "password": "asdt2018" })
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Check properly created
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    user = User.objects.get(email='albert@asdt.eu')
    self.assertTrue(user.group == group)

    # Leave it as it was
    user.delete()

  def test_update_only_group(self):
    
    # Get Token
    self.authenticate("master@asdt.eu", "asdt2019")


    # Create custom user    
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_former = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    user = User.objects.create(email='sergi@asdt.eu', name='Sergi', group=group_former)
    user.set_password('asdt2019')
    
    # Update user
    body = {
      "group": str(group.id)
    }
    response = self.client.put('/{}/user/{}/'.format(settings.PREFIX, user.id), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['email'] == 'sergi@asdt.eu')

    # Check properly created
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    user = User.objects.get(email='sergi@asdt.eu')
    self.assertTrue(user.group == group)

    # Leave it as it was
    user.delete()


  def test_delete(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Create custom user    
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    user = User.objects.create(email='test_delete@asdt.eu', hasGroup=True, group=group)

    # Delete user
    response = self.client.delete('/{}/user/{}/'.format(settings.PREFIX, user.id))
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)
    self.assertTrue( User.objects.filter(email='test_delete@asdt.eu').count() == 0 )






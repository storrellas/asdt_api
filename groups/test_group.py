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

class GroupTestCase(APITestCase):


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

  def test_get(self):
    
    group = Group.objects.get(name='ADMIN_ASDT')

    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                            { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Add groups
    response = self.client.get('/api/v2/groups/{}/'.format(group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

  def test_get_not_allowed(self):
    
    group = Group.objects.get(name='VIEWER_ASDT')

    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                            { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Add groups
    response = self.client.get('/api/v2/groups/{}/'.format(group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertFalse(response_json['success'])

  def test_get_all_admin(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Get All
    response = self.client.get('/api/v2/groups/all/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertEqual(len(response_json['data']), 5)

  def test_get_all_viewer(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "viewer@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Get All
    response = self.client.get('/api/v2/groups/all/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertEqual(len(response_json['data']), 1)

  def test_create(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                            { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Add user to group
    body = { 'name': 'TEST_GROUP' }
    response = self.client.post('/api/v2/groups/', body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check created
    user = User.objects.get(email='admin@asdt.eu')
    self.assertTrue(Group.objects.filter(name='TEST_GROUP').count() > 0)
    group = Group.objects.get(name='TEST_GROUP')
    self.assertEqual(user.group, group.parent)

  def test_create_group_to_add(self):
    
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                            { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Add user to group
    group_to_add = Group.objects.get(name='ADMIN_CHILD_ASDT')
    body = { 'name': 'TEST_GROUP', 'groupToAdd':  group_to_add.id }
    response = self.client.post('/api/v2/groups/', body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check created
    user = User.objects.get(email='admin@asdt.eu')
    self.assertTrue(Group.objects.filter(name='TEST_GROUP').count() > 0)
    group = Group.objects.get(name='TEST_GROUP')
    self.assertEqual(group_to_add, group.parent)


  def test_add_viewer(self):
    
    # Create user with a group assigned
    user = User.objects.create(email='test@asdt.eu', name='test')
    viewer_group = Group.objects.get(name='VIEWER_ASDT')
    viewer_group.users.append(user)
    viewer_group.save()
    user.hasGroup = True
    user.group = viewer_group
    user.save()

    # Target group to which add users
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')

    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                            { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Add user to group
    response = self.client.post('/api/v2/groups/{}/users/{}/'.format(group.id, user.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check groups properly configured
    group_id = user.group.id
    former_group = Group.objects.get(id=group_id)
    self.assertFalse( user in group.users )

    user = User.objects.get(email='test@asdt.eu')
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertEqual( user.group, group )
    self.assertTrue( user in group.users )

    # Delete user from group
    response = self.client.delete('/api/v2/groups/{}/users/{}/'.format(group.id, user.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    user = User.objects.get(email='test@asdt.eu')
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertNotEqual( user.group, group )
    self.assertFalse( user in group.users )

  def test_add_viewer_not_allowed(self):
    
    user = User.objects.get(email='viewer@asdt.eu')
    group = Group.objects.get(name='VIEWER_ASDT')

    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                            { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Add groups
    response = self.client.post('/api/v2/groups/{}/users/{}/'.format(group.id, user.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertFalse(response_json['success'])
  










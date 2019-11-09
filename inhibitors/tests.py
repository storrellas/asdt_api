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
    response = self.client.get('/api/v2/inhibitors/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    print(response_json)
    self.assertTrue(response_json['success'])



  # def test_retrieve(self):
    
  #   group = Group.objects.get(name='ADMIN_ASDT')

  #   # Get Token
  #   self.authenticate("admin@asdt.eu", "asdt2019")

  #   # Add groups
  #   response = self.client.get('/api/v2/groups/{}/'.format(group.id))
  #   self.assertTrue(response.status_code == HTTPStatus.OK)
  #   response_json = json.loads(response.content.decode())
  #   self.assertTrue(response_json['success'])

  # def test_create(self):
    
  #   # Get Token
  #   self.authenticate("admin@asdt.eu", "asdt2019")

  #   # Create group
  #   body = { 'name': 'TEST_GROUP' }
  #   response = self.client.post('/api/v2/groups/', body)
  #   self.assertTrue(response.status_code == HTTPStatus.OK)
  #   response_json = json.loads(response.content.decode())
  #   self.assertTrue(response_json['success'])

  #   # Check created
  #   user = User.objects.get(email='admin@asdt.eu')
  #   self.assertTrue(Group.objects.filter(name='TEST_GROUP').count() > 0)
  #   group = Group.objects.get(name='TEST_GROUP')
  #   self.assertEqual(user.group, group.parent)
    
  #   # Remove resources
  #   user.group.childs.remove(group)
  #   user.group.save()
  #   group.delete()


  # def test_update(self):
  #   # Target group to which add users
  #   group = Group.objects.get(name='ADMIN_CHILD_ASDT')

  #   # Get Token
  #   self.authenticate("admin@asdt.eu", "asdt2019")

  #   # Update group
  #   body = { 'name': 'ADMIN_CHILD_ASDT_UPDATED' }
  #   response = self.client.put('/api/v2/groups/{}/'.format(group.id), body)
  #   self.assertTrue(response.status_code == HTTPStatus.OK)
  #   response_json = json.loads(response.content.decode())
  #   self.assertTrue(response_json['success'])
  #   self.assertTrue(Group.objects.filter(name='ADMIN_CHILD_ASDT_UPDATED').count() > 0)

  #   # Leave it as it was
  #   group = Group.objects.get(name='ADMIN_CHILD_ASDT_UPDATED')
  #   group.name = 'ADMIN_CHILD_ASDT'
  #   group.save()


  # def test_delete(self):
    
  #   # Get Token
  #   self.authenticate("admin@asdt.eu", "asdt2019")

  #   # Delete Group
  #   response = self.client.delete('/api/v2/groups/{}/'.format(delete_group.id))
  #   self.assertTrue(response.status_code == HTTPStatus.OK)
  #   response_json = json.loads(response.content.decode())
  #   self.assertTrue(response_json['success'])
  #   self.assertTrue(Group.objects.filter(name='DELETE_ASDT').count() == 0)
  #   self.assertTrue(Group.objects.filter(name='DELETE_CHILD_ASDT').count() == 0)
  #   user = User.objects.get(email='delete@asdt.eu')
  #   self.assertTrue(user.group == None)








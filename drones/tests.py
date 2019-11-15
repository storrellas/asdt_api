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
from asdt_api import helper_tests
from mongo_dummy import MongoDummy
from .models import *

logger = utils.get_logger()

class TestCase(helper_tests.DeviceTestCase):

  base_url = '/{}/drones/'.format(settings.PREFIX)
  model = Drone

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
    super().list_device()

  def test_retrieve(self):    
    # Retrieve detector
    instance = Drone.objects.get(sn='1')
    super().retrieve_device(instance.id)

  def test_get_model(self):
    # Get token
    self.authenticate('admin@asdt.eu', 'asdt2019')

    # Get Model
    response = self.client.get('/{}/drones/model/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(len(response_json['data']) > 0)

  def test_create_update_delete(self):

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_updated = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Create
    body = {
      'sn' : 'mysn',
      'owner': 'myowner',
      'hide' : True,
      'groups': [ str(group.id) ]
    }

    # Update
    bodyupdated = {
      'sn' : 'mysnupdated',
      'owner': 'myowner',
      'hide' : True,
      'groups': [ str(group_updated.id) ]
    }
    super().create_update_delete_device(body, bodyupdated)

  def test_update_only_group(self):

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_updated = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Create
    body = {
      'sn' : 'mysn',
      'owner': 'myowner',
      'hide' : True,
      'groups': [ str(group.id) ]
    }

    # Update
    bodyupdated = {
      'groups': [ str(group_updated.id) ]
    }
    super().update_only_group_device(body, bodyupdated)

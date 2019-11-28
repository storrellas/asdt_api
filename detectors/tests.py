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

  base_url = '/{}/detectors/'.format(settings.PREFIX_API)
  model = Detector

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

  def test_list_not_allowed(self):
    super().list_device_not_allowed()

  def test_retrieve(self):    
    # Retrieve detector
    instance = Detector.objects.get(name='detector2')
    super().retrieve_device(instance.id)


  def test_retrieve_not_allowed(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Retrieve detector
    detector = Detector.objects.get(name='detector1')

    # Get single
    response = self.client.get('/{}/detectors/{}/'.format(settings.PREFIX_API, detector.id))
    self.assertTrue(response.status_code == HTTPStatus.BAD_REQUEST)

  def test_create_update_delete(self):

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_updated = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Create
    body = {
      'name' : 'myname',
      'password': 'mypassword',
      'location' : {'lat': 12.3, 'lon': 3.2, 'height': 5.4 },
      'groups': [ str(group.id) ]
    }

    # Update
    bodyupdated = {
      'name' : 'mynameupdated',
      'password': 'mypassword',
      'location' : {'lat': 12.3, 'lon': 3.2, 'height': 5.4 },
      'groups': [ str(group_updated.id) ]
    }
    super().create_update_delete_device(body, bodyupdated)

  def test_update_only_group(self):
    
    # Two groups for checking
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_updated = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Create
    body = {
      'name' : 'myname',
      'password': 'mypassword',
      'location' : {'lat': 12.3, 'lon': 3.2, 'height': 5.4 },
      'groups': [ str(group.id) ]
    }

    # Update
    bodyupdated = {
      'groups': [ str(group_updated.id) ]
    }
    super().update_only_group_device(body, bodyupdated)

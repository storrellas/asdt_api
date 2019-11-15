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

  base_url = '/{}/zones/'.format(settings.PREFIX)
  model = Zone

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
    super().test_list()

  def test_retrieve(self):    
    # Retrieve detector
    instance = Zone.objects.get(name='zone1')
    super().test_retrieve(instance.id)

  def test_create_update_delete(self):
    
    # Two groups for checking
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_updated = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Body when creating
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

    # Body when calling updated
    bodyupdated = {
      'name' : 'mynameupdated',
      'center' : {'lat': 12.3, 'lon': 3.2 },
      'radius' : 2,
      'perimiter' : [{'lat': 12.3, 'lon': 3.2 }],
      'maxLat' : 2,
      'maxLon' : 2,
      'minLat' : 2,
      'minLon' : 2,
      'groups': [ str(group_updated.id) ]
    }
    super().test_create_update_delete(body, bodyupdated)



  def test_update_only_group(self):
    
    # Two groups for checking
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_updated = Group.objects.get(name='ADMIN_CHILD2_ASDT')

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

    # Update
    bodyupdated = {
      'groups': [ str(group_updated.id) ]
    }
    super().test_update_only_group(body, bodyupdated)



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
from inhibitors.models import Inhibitor
from detectors.models import Detector
from drones.models import Drone
from zones.models import Zone

logger = utils.get_logger()

class TestCase(helper_tests.ASDTTestCase):

  def setUp(self):
    """
    Called before every test
    """
    logger.info("----------------------------")
    logger.info("--- Generating scenario  ---")
    logger.info("----------------------------")    
    settings.MONGO_DB = 'asdt_test'
    logger.info("DB Generated: {}".format(settings.MONGO_DB))

    mongo_dummy = MongoDummy()
    mongo_dummy.setup(settings.MONGO_DB, settings.MONGO_HOST, int(settings.MONGO_PORT))
    mongo_dummy.generate_scenario()
  
  def test_delete_user(self):
    
    instance = User.objects.get(email='admin_child@asdt.eu')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Delete Group
    response = self.client.delete('/{}/user/{}/'.format(settings.PREFIX, instance.id))
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)

    # Check related entities are there
    self.assertTrue( User.objects.filter(email='admin_child@asdt.eu').count() == 0 )
    self.assertTrue( Group.objects.filter(name='ADMIN_CHILD_ASDT').count() > 0 )

  def test_delete_device(self):
    """
    All devices make use of the same logic
    """
    
    instance = Detector.objects.get(name='detector3')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Delete Group
    response = self.client.delete('/{}/detectors/{}/'.format(settings.PREFIX, instance.id))
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)

    # Check related entities are there
    self.assertTrue( Detector.objects.filter(name='detector3').count() == 0 )
    self.assertTrue( Group.objects.filter(name='ADMIN_CHILD_ASDT').count() > 0 )

  def test_delete_group(self):
    """
    All devices make use of the same logic
    """
    
    instance = Group.objects.get(name='ADMIN_CHILD_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Delete Group
    response = self.client.delete('/{}/groups/{}/'.format(settings.PREFIX, instance.id))
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)

    # Check related entities are there
    self.assertTrue( Group.objects.filter(name='ADMIN_CHILD_ASDT').count() == 0 )
    self.assertTrue( User.objects.filter(email='admin_child@asdt.eu').count() > 0 ) # child
    self.assertTrue( Group.objects.filter(name='ADMIN_ASDT').count() > 0 ) # Parent
    self.assertTrue( Detector.objects.filter(name='detector3').count() > 0 ) # Device
    self.assertTrue( Drone.objects.filter(sn='2').count() > 0 ) # Device
    self.assertTrue( Inhibitor.objects.filter(name='inhibitor2').count() > 0 ) # Device
    self.assertTrue( Zone.objects.filter(name='zone2').count() > 0 ) # Device









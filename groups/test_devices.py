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
from inhibitors.models import Inhibitor
from detectors.models import Detector
from drones.models import Drone
from zones.models import Zone

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
    response = self.client.post('/api/v2/user/authenticate/', 
                            { "email": user, "password": password })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)
  
  def test_add_delete_detector(self):
    
    detector = Detector.objects.get(name='detector4')
    group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add inhibitor to group
    response = self.client.post('/api/v2/groups/{}/devices/detectors/{}/'.format(group.id, detector.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check operation
    detector = Detector.objects.get(name='detector4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertTrue( detector in group.devices.detectors )
    self.assertTrue( group in detector.groups )

    # Remove inhibitor from group
    response = self.client.delete('/api/v2/groups/{}/devices/detectors/{}/'.format(group.id, detector.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check operation
    detector = Detector.objects.get(name='detector4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertFalse( detector in group.devices.detectors )
    self.assertFalse( group in detector.groups )

  def test_add_delete_drone(self):
    
    drone = Drone.objects.get(sn='4')
    group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add inhibitor to group
    response = self.client.post('/api/v2/groups/{}/devices/drones/{}/'.format(group.id, drone.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check operation
    drone = Drone.objects.get(sn='4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertTrue( drone in group.devices.friendDrones )
    self.assertTrue( group in drone.groups )

    # Remove inhibitor from group
    response = self.client.delete('/api/v2/groups/{}/devices/drones/{}/'.format(group.id, drone.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check operation
    drone = Drone.objects.get(sn='4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertFalse( drone in group.devices.friendDrones )
    self.assertFalse( group in drone.groups )

  def test_add_delete_inhibitor(self):
    
    inhibitor = Inhibitor.objects.get(name='inhibitor4')
    group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add inhibitor to group
    response = self.client.post('/api/v2/groups/{}/devices/inhibitors/{}/'.format(group.id, inhibitor.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check operation
    inhibitor = Inhibitor.objects.get(name='inhibitor4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertTrue( inhibitor in group.devices.inhibitors )
    self.assertTrue( group in inhibitor.groups )

    # Remove inhibitor from group
    response = self.client.delete('/api/v2/groups/{}/devices/inhibitors/{}/'.format(group.id, inhibitor.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check operation
    inhibitor = Inhibitor.objects.get(name='inhibitor4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertFalse( inhibitor in group.devices.inhibitors )
    self.assertFalse( group in inhibitor.groups )

  def test_add_delete_zone(self):
    
    zone = Zone.objects.get(name='zone4')
    group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add inhibitor to group
    response = self.client.post('/api/v2/groups/{}/devices/zones/{}/'.format(group.id, zone.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check operation
    zone = Zone.objects.get(name='zone4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertTrue( zone in group.devices.zones )
    self.assertTrue( group in zone.groups )

    # Remove inhibitor from group
    response = self.client.delete('/api/v2/groups/{}/devices/zones/{}/'.format(group.id, zone.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

    # Check operation
    zone = Zone.objects.get(name='zone4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertFalse( zone in group.devices.zones )
    self.assertFalse( group in zone.groups )

  def test_get_group_drones(self):
    admin_group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Request drones
    response = self.client.get('/api/v2/groups/{}/drones/'.format(admin_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

  def test_get_group_detectors(self):
    admin_group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Request detectors
    response = self.client.get('/api/v2/groups/{}/devices/detectors/'.format(admin_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

  def test_get_group_inhibitors(self):
    admin_group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Request inhibitors
    response = self.client.get('/api/v2/groups/{}/devices/inhibitors/'.format(admin_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

  def test_get_group_zones(self):
    admin_group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Request zones
    response = self.client.get('/api/v2/groups/{}/devices/zones/'.format(admin_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])










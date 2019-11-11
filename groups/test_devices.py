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
  
  def test_add_delete_detector(self):
    
    detector = Detector.objects.get(name='detector4')
    group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add inhibitor to group
    response = self.client.post('/{}/groups/{}/devices/detectors/{}/'.format(settings.PREFIX, group.id, detector.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Check operation
    detector = Detector.objects.get(name='detector4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertTrue( detector in group.devices.detectors )
    self.assertTrue( group in detector.groups )

    # Remove inhibitor from group
    response = self.client.delete('/{}/groups/{}/devices/detectors/{}/'.format(settings.PREFIX, group.id, detector.id), {})
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)

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
    response = self.client.post('/{}/groups/{}/devices/drones/{}/'.format(settings.PREFIX, group.id, drone.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Check operation
    drone = Drone.objects.get(sn='4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertTrue( drone in group.devices.friendDrones )
    self.assertTrue( group in drone.groups )

    # Remove inhibitor from group
    response = self.client.delete('/{}/groups/{}/devices/drones/{}/'.format(settings.PREFIX, group.id, drone.id), {})
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)

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
    response = self.client.post('/{}/groups/{}/devices/inhibitors/{}/'.format(settings.PREFIX, group.id, inhibitor.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Check operation
    inhibitor = Inhibitor.objects.get(name='inhibitor4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertTrue( inhibitor in group.devices.inhibitors )
    self.assertTrue( group in inhibitor.groups )

    # Remove inhibitor from group
    response = self.client.delete('/{}/groups/{}/devices/inhibitors/{}/'.format(settings.PREFIX, group.id, inhibitor.id), {})
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)

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
    response = self.client.post('/{}/groups/{}/devices/zones/{}/'.format(settings.PREFIX, group.id, zone.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Check operation
    zone = Zone.objects.get(name='zone4')
    group = Group.objects.get(name='ADMIN_ASDT')
    self.assertTrue( zone in group.devices.zones )
    self.assertTrue( group in zone.groups )

    # Remove inhibitor from group
    response = self.client.delete('/{}/groups/{}/devices/zones/{}/'.format(settings.PREFIX, group.id, zone.id), {})
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)

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
    response = self.client.get('/{}/groups/{}/drones/'.format(settings.PREFIX, admin_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)

  def test_get_group_detectors(self):
    admin_group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Request detectors
    response = self.client.get('/{}/groups/{}/devices/detectors/'.format(settings.PREFIX, admin_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)

  def test_get_group_inhibitors(self):
    admin_group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Request inhibitors
    response = self.client.get('/{}/groups/{}/devices/inhibitors/'.format(settings.PREFIX, admin_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)

  def test_get_group_zones(self):
    admin_group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Request zones
    response = self.client.get('/{}/groups/{}/devices/zones/'.format(settings.PREFIX, admin_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)










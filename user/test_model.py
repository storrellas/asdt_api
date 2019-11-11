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
from asdt_api import tests
from mongo_dummy import MongoDummy
from .models import *

logger = utils.get_logger()

class UserModelTestCase(tests.ASDTTestCase):


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

  def test_user_has_power_over(self):
    admin_user = User.objects.get(email='admin@asdt.eu')
    admin_child_user = User.objects.get(email='admin_child@asdt.eu')
    self.assertTrue(admin_user.has_power_over(admin_child_user))
    self.assertFalse(admin_user.has_power_over(admin_user))





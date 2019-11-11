from django.test import TestCase

# Create your tests here.
import csv, json
from http import HTTPStatus

from django.test import TestCase, Client
from django.http import HttpRequest
from django.conf import settings
from rest_framework.test import APITestCase


# Projet imports
from asdt_api import utils
from mongo_dummy import MongoDummy

logger = utils.get_logger()

class ASDTTestCase(APITestCase):

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
    super().setUp()

  def authenticate(self, user, password):
    # Get token
    response = self.client.post('/{}/user/authenticate/'.format(settings.PREFIX), 
                            { "email": user, "password": password })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

class DeviceTestCase(ASDTTestCase):

  base_url = None
  base_url_trimmed = None


  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # Remove last trailing slash
    if self.base_url is not None:
      self.base_url_trimmed = self.base_url[:-1] if self.base_url[-1] == '/' else self.base_url

  def setUp(self):
    """
    Called before every test
    """
    super().setUp()

  def test_list(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get All
    response = self.client.get(self.base_url)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

  def test_retrieve(self, id):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get single
    response = self.client.get('{}/{}/'.format(self.base_url_trimmed, id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

import json
from http import HTTPStatus
import datetime

# Django imports
from django.test import TestCase, Client
from django.http import HttpRequest
from django.conf import settings
from rest_framework.test import APITestCase
from unittest.mock import patch

# Project imports
from asdt_api import utils
from mongo_dummy import MongoDummy
from user.models import User
from groups.models import Group
from logs.models import Log, LogCenterPoint, LogBoundingBox
from asdt_api.models import Location

logger = utils.get_logger()

class LogsTestCase(APITestCase):


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

    # Add logs for user with today date
    logger.info("Creating logs for today")
    user = User.objects.get(email='admin@asdt.eu')
    route = mongo_dummy.default_route()
    Log.objects.create(dateIni=datetime.datetime.now(), 
                        dateFin=datetime.datetime.now(),
                        model='ABC', sn='1', productId=1234,
                        detectors=user.group.devices.detectors,
                        driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                        maxHeight=12, distanceTraveled=12, distanceToDetector=12,
                        centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                        boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3), route=route)


  def setUp(self):
    """
    Called before every test
    """
    pass

  def test_logs(self):

    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Get Logs
    response = self.client.get('/api/v2/logs/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['success'], True)    
    self.assertEqual(len(response_json['data']), 1)

  def test_logs_bydate(self):
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Get Logs
    url_params = {
      "dateIni": "2019-08-01T23:00:00.000Z",
      "dateFin": "2019-11-01T00:00:00.000Z"
    }
    response = self.client.get('/api/v2/logs/', url_params)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['success'], True)
    self.assertEqual(len(response_json['data']), 3)

    # Get Logs
    url_params = {
      "dateIni": "2019-10-01T23:00:00.000Z",
      "dateFin": "2019-11-01T00:00:00.000Z"
    }
    response = self.client.get('/api/v2/logs/', url_params)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['success'], True)
    self.assertEqual(len(response_json['data']), 2)

  def test_logs_bypage(self):
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Get Logs
    url_params = {
      "dateIni": "2019-08-01T23:00:00.000Z",
      "dateFin": "2019-11-01T00:00:00.000Z",
      "page": 0
    }
    response = self.client.get('/api/v2/logs/', url_params)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['success'], True)
    self.assertEqual(len(response_json['data']), 3)
    log_id = response_json['data'][0]['id']

    # Get Logs
    url_params = {
      "dateIni": "2019-10-01T23:00:00.000Z",
      "dateFin": "2019-11-01T00:00:00.000Z",
      "page" : 1
    }
    response = self.client.get('/api/v2/logs/', url_params)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['success'], True)
    self.assertEqual(len(response_json['data']), 0)

    # Get by ID
    response = self.client.get('/api/v2/logs/{}/'.format(log_id))
    self.assertTrue(response.status_code == HTTPStatus.OK)


    # Get KML
    response = self.client.get('/api/v2/logs/{}/kml/'.format(log_id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    self.assertEqual(response.get('Content-Type'), 'application/xml')

  def test_logs_bysn(self):
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "admin@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Get Logs
    url_params = {
      "dateIni": "2019-08-01T23:00:00.000Z",
      "dateFin": "2019-11-01T00:00:00.000Z",
      "sn": "1"
    }
    response = self.client.get('/api/v2/logs/', url_params)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['success'], True)
    self.assertEqual(len(response_json['data']), 1)

    # Get Logs
    url_params = {
      "dateIni": "2019-10-01T23:00:00.000Z",
      "dateFin": "2019-11-01T00:00:00.000Z",
      "sn" : "6"
    }
    response = self.client.get('/api/v2/logs/', url_params)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['success'], True)
    self.assertEqual(len(response_json['data']), 0)


  def test_logs_not_allowed(self):
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                                { "email": "master@asdt.eu", "password": "asdt2019" })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

    # Get Logs
    url_params = {
      "dateIni": "2019-08-01T23:00:00.000Z",
      "dateFin": "2019-11-01T00:00:00.000Z"
    }
    response = self.client.get('/api/v2/logs/', url_params)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(response_json['success'], False)



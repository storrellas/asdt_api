# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
parent_parentdir = os.path.dirname(parentdir)
sys.path.append(parent_parentdir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asdt_api.settings")

# Python imports
import unittest
import threading
import datetime
from time import sleep

# Testing files
from common import DetectorCoder, LogMessage, LogLocationMessage
from common.utils import get_logger

# Websocket
import mongoengine


# Tornado imports
import asyncio
import tornado
import requests
from tornado.platform.asyncio import AnyThreadEventLoopPolicy
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.websocket import WebSocketHandler

# Project import
from django.conf import settings
from message_broker_detection import WSMessageDetectionBroker
from common import DetectorCoder, LogMessage, LogLocationMessage

# # Detector client/server
# from client import WSDetectorClient, DroneFlight
# from server import WSHandler, WSConnectionRepository

# Import models
from detectors.models import Detector
from user.models import User
from logs.models import Log, LogRoute

# Imports for test
from client import DroneFlight
from ws_thread import WSHandlerMockup, WSUserClientMockup, WSDetectorClientMockup, WSServerThread

logger = get_logger()

# Configuration - client
API_URL = 'http://localhost:8080'
API_DETECTOR_AUTH_URL = 'http://localhost:8080/api/v3/detectors/authenticate/'
API_USER_AUTH_URL = 'http://localhost:8080/api/v3/user/authenticate/'

# URL To connect WS
WS_PORT = 8081
WS_URL = 'ws://localhost:{}/{}/'.format(WS_PORT, settings.PREFIX_WS)

class TestCase(unittest.TestCase):

  ioloop_thread = None  

  @classmethod
  def setUpClass(cls):
    """
    Called once in every suite
    """
    super().setUpClass()

    # Open mongo connection
    mongoengine.connect(settings.MONGO_DB, host=settings.MONGO_HOST, port=int(settings.MONGO_PORT))
    logger.info("Connected MONGODB against mongodb://{}:{}/{}".format(settings.MONGO_HOST, settings.MONGO_PORT, settings.MONGO_DB))

    # See http://www.tornadoweb.org/en/stable/asyncio.html#tornado.platform.asyncio.AnyThreadEventLoopPolicy
    asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

    # Start thread
    cls.ioloop_thread = WSServerThread(WS_PORT, WS_URL)
    cls.ioloop_thread.start()

    # Wait until WS Server is running
    cls.ioloop_thread.wait_for_server()
    logger.info("Server ready!")

  @classmethod
  def tearDownClass(cls):
    """
    Called once in every suite
    """
    # Request for termination of both client and server
    cls.ioloop_thread.request_terminate()
    cls.ioloop_thread.join()

  def setUp(self):
    # Reset event
    self.ioloop_thread.detector_client.client_idle.clear()
    self.ioloop_thread.server_idle.clear()

  def check_range(self, target, candidate):
    return target - 1 < candidate < target + 1

  def check_location(self, target, candidate):
    cond1 = self.check_range(target.lat, candidate.lat)
    cond2 = self.check_range(target.lon, candidate.lon)
    return cond1 and cond2

  def test_detector_login(self):
    
    # Login
    detector = Detector.objects.get(name='detector2')
    detector.set_password('asdt2019')
    result, token = self.ioloop_thread.login_detector_client('{}/api/v3/detectors/authenticate/'.format(API_URL), str(detector.id), 'asdt2019')
    self.assertTrue(result)

  def test_detector_login_fail(self):
    
    # Login
    detector = Detector.objects.get(name='detector2')
    detector.set_password('asdt2019')
    result, token = self.ioloop_thread.login_detector_client('{}/api/v3/detectors/authenticate/'.format(API_URL), str(detector.id), 'asdt201')
    self.assertFalse(result)

  def test_detector_login_token(self):
    
    # Login
    detector = Detector.objects.get(name='detector2')
    detector.set_password('asdt2019')
    result, token = self.ioloop_thread.login_detector_client('{}/api/v3/detectors/authenticate/'.format(API_URL), str(detector.id), 'asdt2019')
    self.assertTrue(result)

    # Launches detector client
    self.ioloop_thread.launch_detector_client()
    self.ioloop_thread.wait_for_detector_client()
    self.assertTrue( self.ioloop_thread.detector_client.is_ws_connected() )

    # Wait for server to reject client
    self.ioloop_thread.wait_for_server()

    # Check detector client is connected
    self.assertTrue( self.ioloop_thread.detector_client.is_ws_connected() )

    # Check connection present in server
    ws_conn = self.ioloop_thread.repository.find_by_id(str(detector.id))
    self.assertTrue( ws_conn is not None )

    # Close detector client
    self.ioloop_thread.detector_client.close()

    # Wait for server to close connection
    self.ioloop_thread.wait_for_server()

    # Check detector client not connected
    self.assertFalse( self.ioloop_thread.detector_client.is_ws_connected() )

    # Check connection NOT present in server
    ws_conn = self.ioloop_thread.repository.find_by_id(str(detector.id))
    self.assertTrue( ws_conn is None )

  def test_detector_login_token_fails(self):

    # Login
    detector = Detector.objects.get(name='detector2')
    detector.set_password('asdt2019')
    result, token = self.ioloop_thread.login_detector_client('{}/api/v3/detectors/authenticate/'.format(API_URL), str(detector.id), 'asdt2019')
    self.assertTrue(result)

    # Launches detector client - Sends token to server to authenticate
    self.ioloop_thread.detector_client.token = '123'
    self.ioloop_thread.launch_detector_client()
    self.ioloop_thread.wait_for_detector_client()

    # Wait for server to reject client
    self.ioloop_thread.wait_for_server()

    # Check detector client is closed
    sleep(0.01) # NOTE: The time while client checks that socket is closed
                # Not very elegant
    self.assertFalse( self.ioloop_thread.detector_client.is_ws_connected() )
    
  def test_detector_send_detection(self):

    # Login
    detector = Detector.objects.get(name='detector2')
    detector.set_password('asdt2019')
    result, token = self.ioloop_thread.login_detector_client('{}/api/v3/detectors/authenticate/'.format(API_URL), str(detector.id), 'asdt2019')
    self.assertTrue(result)

    # Launch detector client
    self.ioloop_thread.launch_detector_client()
    self.ioloop_thread.wait_for_detector_client()
    self.assertTrue( self.ioloop_thread.detector_client.is_ws_connected() )

    # Wait for server to process client
    self.ioloop_thread.wait_for_server()

    # Send detection
    sn = '000000000000001'
    lat = 41.7
    lon = 1.8
    drone_flight = DroneFlight(sn, lat, lon)


    # Remove all Logs with sn for testing
    Log.objects.filter(sn=sn).delete()
    self.assertEqual(Log.objects.filter(sn=sn).count(), 0)

    # Send FIRST message
    ########################
    detection_log = drone_flight.get_detection_log()
    self.ioloop_thread.detector_client.send_detection_log(detection_log)
    # Wait for server to process message
    self.ioloop_thread.wait_for_server()

    # Check whether log has been created  
    self.assertEqual(Log.objects.filter(sn=sn).count(), 1)
    log = Log.objects.get(sn=sn)
    self.assertTrue( log.distanceToDetector > 0 )
    self.assertTrue( log.distanceTraveled == 0 )
    self.assertTrue( log.maxHeight > 0 )

    # Check route
    self.assertEqual(len(log.route), 1)
    target = LogRoute(lat=lat,lon=lon)
    self.assertTrue(self.check_location(target, log.route[0]) )

    # Send SECOND message
    ########################
    detection_log = drone_flight.get_detection_log()
    self.ioloop_thread.detector_client.send_detection_log(detection_log)
    # Wait for server to process message
    self.ioloop_thread.wait_for_server()

    # Check whether log has been created  
    self.assertEqual(Log.objects.filter(sn=sn).count(), 1)
    log = Log.objects.get(sn=sn)
    self.assertTrue( log.distanceToDetector > 0 )
    self.assertTrue( log.distanceTraveled > 0 )
    self.assertTrue( log.maxHeight > 0 )

    # Check route
    self.assertEqual(len(log.route), 2)
    target = LogRoute(lat=lat,lon=lon)
    self.assertTrue(self.check_location(target, log.route[1]) )

    # Check DroneFlight is marked as finished
    ########################
    dateFin = datetime.datetime.now() - datetime.timedelta(minutes=1)
    log = Log.objects.get(sn=sn)
    log.dateFin = dateFin
    log.save()
    self.assertEqual( log.dateFin, dateFin)

    log_message = self.ioloop_thread.broker_detection.get_log(sn)
    lastUpdate = dateFin
    log_message.lastUpdate = lastUpdate


    # Simulate logs update
    self.ioloop_thread.broker_detection.logs_update()

    # Check logs_update
    log = Log.objects.get(sn=sn)
    self.assertNotEqual( log.dateFin, lastUpdate)

    # Close detector client
    self.ioloop_thread.detector_client.close()





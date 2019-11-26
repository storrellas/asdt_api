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
from http import HTTPStatus
import json

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
from mongo_dummy import MongoDummy
from django.conf import settings
from message_broker import WSMessageBroker
from common import DetectorCoder, LogMessage, LogLocationMessage

# Detector client/server
from detector_sim import DetectorWSClient, DroneFlight
from server import WSHandler, WSConnectionRepository

# Import models
from detectors.models import Detector
from logs.models import Log, LogRoute

logger = get_logger()

# Configuration - server
WS_PORT = 8081
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB = 'asdt'
# Configuration - client
API_AUTH_URL = 'http://localhost:8080/api/v3/detectors/authenticate/'
WS_URL = 'ws://localhost:8081/api'

EVENT_WAIT_TIMEOUT = 10 # Number of seconds before continue

class WSHandlerMockup(WSHandler):
  
  server_idle = None

  def initialize(self, repository, broker, secret_key, server_idle):
    super().initialize(repository, broker, secret_key)
    self.server_idle = server_idle

  def on_message(self, message):    
    super().on_message(message)
    self.server_idle.set()

  def on_close(self):    
    super().on_close()
    self.server_idle.set()

class DetectorWSClientMockup(DetectorWSClient):
  
  client_idle = None

  def __init__(self, ws_url = None, drone_flight = None):
    super().__init__(ws_url, drone_flight)
    self.client_idle = threading.Event()

  async def connect(self):
    await super().connect()
    # Signal client is ready
    self.client_idle.set()

  def on_message_callback(self, msg):    
    super().on_message_callback(msg)
    self.client_idle.set()

class WSServerThread(threading.Thread):
  """
  Runs WS Server in a separated thread
  """

  # Thread synchro
  server_idle = None

  # Tornado
  ioloop = None
  client = None
  repository = None
  broker = None

  def __init__(self):
    super().__init__()
    self.server_idle = threading.Event()

  def run(self):
    # Store ioloop instance
    self.ioloop = IOLoop.instance()


    # Create web application
    self.repository = WSConnectionRepository()
    self.broker = WSMessageBroker()
    application = tornado.web.Application([
      (r'/api', WSHandlerMockup, dict(repository=self.repository, broker=self.broker, 
                                      secret_key=settings.SECRET_KEY, server_idle=self.server_idle)),
    ])

    # Starting WS Server
    logger.info("Started Data Channel WS 0.0.0.0@{}".format(WS_PORT))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(WS_PORT)

    # Create client
    self.client = DetectorWSClientMockup(WS_URL)

    # Used to signal server is ready
    self.server_idle.set()

    # Start instance
    self.ioloop.start()

  def wait_for_server(self):
    """
    Blocking function to test whether WS Server is ready
    """
    self.server_idle.wait(EVENT_WAIT_TIMEOUT)
    if self.server_idle.isSet() == False:
      return False
    self.server_idle.clear()
    return True

  def wait_for_client(self):
    """
    Blocking function to test whether WS Server is ready
    """
    self.client.client_idle.wait(EVENT_WAIT_TIMEOUT)
    if self.client.client_idle.isSet() == False:
      return False
    self.client.client_idle.clear()
    return True

  def login_client(self, url, detector_id, password):
    return self.client.login(url, detector_id, password)

  def launch_client(self):
    """
    Launches client
    """
    self.ioloop.spawn_callback(self.client.connect)
    self.wait_for_client()

  def request_terminate(self):
    """
    Requests for WS Server termination
    """
    logger.info('Closing WS Server ...')
    # Call callback in the next ioloo iteration
    self.ioloop.spawn_callback(self._terminate)
    
  def _terminate(self):
    """
    WS Server termination
    """
    logger.info("Terminated ioloop")
    self.ioloop.stop()
    logger.info('DONE!')



class TestCase(unittest.TestCase):

  ioloop_thread = None  

  @classmethod
  def setUpClass(cls):
    """
    Called once in every suite
    """
    super().setUpClass()

    # Open mongo connection
    mongoengine.connect(MONGO_DB, host=MONGO_HOST, port=int(MONGO_PORT))
    logger.info("Connected MONGODB against mongodb://{}:{}/{}".format(MONGO_HOST, MONGO_PORT, MONGO_DB))

    # See http://www.tornadoweb.org/en/stable/asyncio.html#tornado.platform.asyncio.AnyThreadEventLoopPolicy
    asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

    # Start thread
    cls.ioloop_thread = WSServerThread()
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
    self.ioloop_thread.client.client_idle.clear()
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
    result, token = self.ioloop_thread.login_client(API_AUTH_URL, str(detector.id), 'asdt2019')
    self.assertTrue(result)

  def test_detector_login_fail(self):
    
    # Login
    detector = Detector.objects.get(name='detector2')
    detector.set_password('asdt2019')
    result, token = self.ioloop_thread.login_client(API_AUTH_URL, str(detector.id), 'asdt201')
    self.assertFalse(result)

  def test_detector_login_token(self):
    
    # Login
    detector = Detector.objects.get(name='detector2')
    detector.set_password('asdt2019')
    result, token = self.ioloop_thread.login_client(API_AUTH_URL, str(detector.id), 'asdt2019')
    self.assertTrue(result)

    # Launches client
    self.ioloop_thread.launch_client()
    self.assertTrue( self.ioloop_thread.client.is_ws_connected() )

    # Wait for server to reject client
    self.ioloop_thread.wait_for_server()

    # Wait for client to close connection
    self.ioloop_thread.wait_for_client()

    # Check client is connected
    self.assertTrue( self.ioloop_thread.client.is_ws_connected() )

    # Check connection present in server
    ws_conn = self.ioloop_thread.repository.find_by_id(str(detector.id))
    self.assertTrue( ws_conn is not None )

    # Close client
    self.ioloop_thread.client.close()

    # Wait for server to close connection
    self.ioloop_thread.wait_for_server()

    # Check client not connected
    self.assertFalse( self.ioloop_thread.client.is_ws_connected() )

    # Check connection NOT present in server
    ws_conn = self.ioloop_thread.repository.find_by_id(str(detector.id))
    self.assertTrue( ws_conn is None )

  def test_detector_login_token_fails(self):

    # Login
    detector = Detector.objects.get(name='detector2')
    detector.set_password('asdt2019')
    result, token = self.ioloop_thread.login_client(API_AUTH_URL, str(detector.id), 'asdt2019')
    self.assertTrue(result)

    # Launches client - Sends token to server to authenticate
    self.ioloop_thread.client.token = '123'
    self.ioloop_thread.launch_client()

    # Wait for server to reject client
    self.ioloop_thread.wait_for_server()

    # Wait for client to close connection
    self.ioloop_thread.wait_for_client()

    # Check client is closed
    sleep(0.01) # NOTE: The time while client checks that socket is closed
                # Not very elegant
    self.assertFalse( self.ioloop_thread.client.is_ws_connected() )
    
  def test_detector_send_detection(self):

    # Login
    detector = Detector.objects.get(name='detector2')
    detector.set_password('asdt2019')
    result, token = self.ioloop_thread.login_client(API_AUTH_URL, str(detector.id), 'asdt2019')
    self.assertTrue(result)

    # Launch client
    self.ioloop_thread.launch_client()
    self.assertTrue( self.ioloop_thread.client.is_ws_connected() )

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
    self.ioloop_thread.client.send_detection_log(detection_log)
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
    self.ioloop_thread.client.send_detection_log(detection_log)
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

    log_message = self.ioloop_thread.broker.get_log(sn)
    lastUpdate = dateFin
    log_message.lastUpdate = lastUpdate


    # Simulate logs update
    self.ioloop_thread.broker.logs_update()

    # Check logs_update
    log = Log.objects.get(sn=sn)
    self.assertNotEqual( log.dateFin, lastUpdate)


    # Close client
    self.ioloop_thread.client.close()


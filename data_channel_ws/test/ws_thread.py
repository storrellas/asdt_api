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
from django.conf import settings
from message_broker_detection import WSMessageDetectionBroker
from common import DetectorCoder, LogMessage, LogLocationMessage

# Detector client/server
from client import WSDetectorClient, WSUserClient, DroneFlight
from server import WSHandler, WSConnectionRepository

# Import models
from detectors.models import Detector
from user.models import User
from logs.models import Log, LogRoute

logger = get_logger()

# Configuration - server




EVENT_WAIT_TIMEOUT = 10 # Number of seconds before continue

class WSHandlerMockup(WSHandler):
  
  server_idle = None

  def initialize(self, repository, broker_detection, secret_key, server_idle):
    super().initialize(repository, broker_detection, secret_key)
    self.server_idle = server_idle

  def on_message(self, message):    
    super().on_message(message)
    self.server_idle.set()

  def on_close(self):    
    super().on_close()
    self.server_idle.set()

class WSDetectorClientMockup(WSDetectorClient):
  
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

class WSUserClientMockup(WSUserClient):
  
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


  # Config for client/server
  ws_url = None
  ws_port = None

  # Tornado - internal variables
  ioloop = None
  detector_client = None
  user_client = None
  repository = None
  broker_detection = None



  def __init__(self, ws_port, ws_url):
    super().__init__()
    self.server_idle = threading.Event()
    self.ws_port = ws_port
    self.ws_url = ws_url

  def run(self):
    # Store ioloop instance
    self.ioloop = IOLoop.instance()


    # Create web application
    self.repository = WSConnectionRepository()
    self.broker_detection = WSMessageDetectionBroker()
    application = tornado.web.Application([
      (r'/{}/'.format(settings.PREFIX_WS), WSHandlerMockup, dict(repository=self.repository, broker_detection=self.broker_detection, 
                                      secret_key=settings.SECRET_KEY, server_idle=self.server_idle)),
    ])

    # Starting WS Server
    logger.info("Started Data Channel WS 0.0.0.0@{}".format(self.ws_port))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(self.ws_port)

    # Create client
    self.detector_client = WSDetectorClientMockup(self.ws_url)
    self.user_client = WSDetectorClientMockup(self.ws_url)

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

  def wait_for_detector_client(self):
    """
    Blocking function to test whether WS Server is ready
    """
    self.detector_client.client_idle.wait(EVENT_WAIT_TIMEOUT)
    if self.detector_client.client_idle.isSet() == False:
      return False
    self.detector_client.client_idle.clear()
    return True

  def wait_for_user_client(self):
    """
    Blocking function to test whether WS Server is ready
    """
    self.user_client.client_idle.wait(EVENT_WAIT_TIMEOUT)
    if self.user_client.client_idle.isSet() == False:
      return False
    self.user_client.client_idle.clear()
    return True

  def login_detector_client(self, url, detector_id, password):
    return self.detector_client.login(url, {'id': detector_id, 'password': password})

  def login_user_client(self, url, email, password):
    return self.user_client.login(url, {'email': email, 'password': password})

  def launch_detector_client(self):
    """
    Launches client
    """
    self.ioloop.spawn_callback(self.detector_client.connect)
    self.wait_for_detector_client()

  def launch_user_client(self):
    """
    Launches client
    """
    self.ioloop.spawn_callback(self.user_client.connect)
    self.wait_for_user_client()

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

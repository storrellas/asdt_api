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
from time import sleep


# Testing files
from common import DetectorCoder, LogMessage, LogLocationMessage
from common.utils import get_logger

# Tornado imports
import asyncio
import tornado
from tornado.platform.asyncio import AnyThreadEventLoopPolicy
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.websocket import WebSocketHandler

# Project import
from mongo_dummy import MongoDummy
from django.conf import settings
from message_broker import WSMessageBroker
from server import WSHandler, WSConnectionReposirory


logger = get_logger()

class WSServerThread(threading.Thread):
  """
  Runs WS Server in a separated thread
  """

  ready_request = None  
  ioloop = None

  def __init__(self):
    super().__init__()
    self.ready_request = threading.Event()

  def run(self):
    # Create web application
    repository = WSConnectionReposirory()
    broker = WSMessageBroker()
    application = tornado.web.Application([
      (r'/api', WSHandler, dict(repository=repository, broker=broker)),
    ])

    # Starting WS Server
    WS_PORT = 8081
    logger.info("Started Data Channel WS 0.0.0.0@{}".format(WS_PORT))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(WS_PORT)

    # # Checks latest activity on every connection
    # PeriodicCallback(repository.keep_alive_connection_repository, 
    #                   KEEP_ALIVE_CONNECTION_PERIOD).start()
    # PeriodicCallback(broker.logs_update, 
    #                   LOGS_UPDATE_PERIOD).start()

    # Used to signal others we are ready
    self.ready_request.set()

    # Store ioloop instance
    self.ioloop = IOLoop.instance()
    # Start instance
    self.ioloop.start()

  def wait_for_ready(self):
    """
    Blocking function to test whether WS Server is ready
    """
    while self.ready_request.isSet() == False:
      logger.info("WS Server is now ready")
      sleep(0.05)

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

  ws_thread = None

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

    # See http://www.tornadoweb.org/en/stable/asyncio.html#tornado.platform.asyncio.AnyThreadEventLoopPolicy
    asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

    # Start thread
    cls.ws_thread = WSServerThread()
    cls.ws_thread.start()

    # Wait until WS Server is running
    cls.ws_thread.wait_for_ready()

  @classmethod
  def tearDownClass(cls):
    """
    Called once in every suite
    """
    # Request for termination
    cls.ws_thread.request_terminate()
    cls.ws_thread.join()

  def test_coder_decoder(self):
    print("MyTestsAreRunning")
    self.assertTrue(True)







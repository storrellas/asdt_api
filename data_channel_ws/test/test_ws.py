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

    self.ready_request.set()
    self.ioloop = IOLoop.instance()
    self.ioloop.start()

  def wait_for_ready(self):
    """
    Blocking function to test whether WS Server is ready
    """
    while ws_thread.ready_request.isSet() == False:
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

  def test_coder_decoder(self):

    # See http://www.tornadoweb.org/en/stable/asyncio.html#tornado.platform.asyncio.AnyThreadEventLoopPolicy
    asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

    ws_thread = WSServerThread()
    ws_thread.start()

    while ws_thread.ready_request.isSet() == False:
      logger.info("WSReady")
      sleep(0.5)

    logger.info("Set")
    ws_thread.request_terminate()
    ws_thread.join()







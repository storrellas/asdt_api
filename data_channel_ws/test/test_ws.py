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
from server import WSHandler, WSConnectionReposirory

# Import models
from detectors.models import Detector

logger = get_logger()

# Configuration - server
WS_PORT = 8081
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB = 'asdt'
# Configuration - client
API_AUTH_URL = 'http://localhost:8080/api/v3/detectors/authenticate/'
WS_URL = 'ws://localhost:8081/api'

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
    # #############
    # mongoengine.connect('asdt_test', host='localhost', port=27017)
    # logger.info("Connected MONGODB against mongodb://{}:{}/{}".format(settings.MONGO_HOST, settings.MONGO_PORT, settings.MONGO_DB))
    # #############

    # Create web application
    repository = WSConnectionReposirory()
    broker = WSMessageBroker()
    application = tornado.web.Application([
      (r'/api', WSHandler, dict(repository=repository, broker=broker)),
    ])

    # Starting WS Server
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
    self.ready_request.wait()

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
    # logger.info("----------------------------")
    # logger.info("--- Generating scenario  ---")
    # logger.info("----------------------------")    
    # settings.MONGO_DB = 'asdt_test'
    # logger.info("DB Generated: {}".format(settings.MONGO_DB))

    # mongo_dummy = MongoDummy()
    # mongo_dummy.setup(settings.MONGO_DB, settings.MONGO_HOST, int(settings.MONGO_PORT))
    # mongo_dummy.generate_scenario()

    # Open mongo connection
    mongoengine.connect(MONGO_DB, host=MONGO_HOST, port=int(MONGO_PORT))
    logger.info("Connected MONGODB against mongodb://{}:{}/{}".format(MONGO_HOST, MONGO_PORT, MONGO_DB))

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



  def test_detector_message(self):
    print("MyTestsAreRunning")
    self.assertTrue(True)
    
    # Login
    detector = Detector.objects.get(name='detector2')
    detector.set_password('asdt2019')

    sn = '000000000000001'
    lat = 41.7
    lon = 1.8
    drone_flight = DroneFlight(sn, lat, lon)
    client = DetectorWSClient(WS_URL, drone_flight)
    result, token = client.login(API_AUTH_URL, str(detector.id), 'asdt2019')

    # # Create WS connection
    # ws = websocket_client.create_connection(WS_URL)
    # print("CONNECTED", ws.connected)
    # print("Sending <token> ...")
    # ws.send(token)
    # print("Sent")


    # print("Receiving...")
    # result =  ws.recv()
    # print("Received '%s'" % result)

    
    # # Create log
    # driverLocation = LogLocationMessage(lat=41.2, lon=2.3)
    # droneLocation = LogLocationMessage(lat=41.2, lon=2.3, fHeight=8.8)
    # homeLocation = LogLocationMessage(lat=41.2, lon=2.3)
    # log = LogMessage(sn='111BBBBBBBBB16', driverLocation=driverLocation,
    #                   droneLocation=droneLocation, homeLocation=homeLocation,
    #                   productId=16)

    # # Encode frame
    # coder = DetectorCoder()
    # encoded = coder.encode( log ) 

    # # Sedni
    # print("Sending <log> ...")
    # ws.send(encoded)
    # print("Sent")

    # # Wait for ok
    # print("Receiving...")
    # result =  ws.recv()
    # print("Received '%s'" % result)
    



# if __name__ == "__main__":
#     # See http://www.tornadoweb.org/en/stable/asyncio.html#tornado.platform.asyncio.AnyThreadEventLoopPolicy
#     asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

#     # logger.info("----------------------------")
#     # logger.info("--- Generating scenario  ---")
#     # logger.info("----------------------------")    
#     # #settings.MONGO_DB = 'asdt_test'
#     # logger.info("DB Generated: {}".format(settings.MONGO_DB))

#     # mongo_dummy = MongoDummy()
#     # mongo_dummy.setup(settings.MONGO_DB, settings.MONGO_HOST, int(settings.MONGO_PORT))
#     # mongo_dummy.generate_scenario()

#     mongoengine.connect(MONGO_DB, host=MONGO_HOST, port=int(MONGO_PORT))
#     logger.info("Connected MONGODB against mongodb://{}:{}/{}".format(MONGO_HOST, MONGO_PORT, MONGO_DB))

#     # Start thread
#     ws_thread = WSServerThread()
#     ws_thread.start()

#     # Wait until WS Server is running
#     ws_thread.wait_for_ready()

#     ##################################
#     ##################################
#     ##################################


#     result, token = DetectorWSClient.login_request(API_AUTH_URL, '5dda8c7ff161a4bdd05f98f7', 'asdt2019')
#     print(token)


    
#     ws = websocket_client.create_connection(WS_URL)
#     print("CONNECTED", ws.connected)
#     print("Sending <token> ...")
#     ws.send(token)
#     print("Sent")


#     print("Receiving...")
#     result =  ws.recv()
#     print("Received '%s'" % result)


#     ##################################
#     ##################################
#     ##################################

#     # Request for termination
#     ws_thread.request_terminate()
#     ws_thread.join()







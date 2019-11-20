# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Python imports
import tornado
import signal
from tornado.websocket import WebSocketHandler
import requests
from http import HTTPStatus
import jwt

# Mongoengine connect
import mongoengine

# Project imports
from common.utils import get_logger
from common import DetectorCoder
from models import ConnectionLog
from detectors.models import Detector

# Create logger
logger = get_logger()
logger.propagate = False


# Configuration
API_USER_INFO = 'http://asdtdev.mooo.com/api/user/info'
#API_USER_INFO = 'http://localhost:8081/api/v3/user/info'
WS_PORT = 8081
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB = 'asdt'

class DetectorConnection:
  """
  Class to store info about a connection
  """
  host = None
  id = None
  logged = False
  ws_handler = None
  msg = None

  def __init__(self, ws_handler = None, host = None, id = None):
    self.ws_handler = ws_handler
    self.host = host
    self.id = id

class WSConnectionReposirory:

  __detector_conn_list = []

  def add(self, detector_conn: DetectorConnection):
    """
    Adds a client
    """
    self.__detector_conn_list.append(detector_conn)

  def remove(self, detector_conn: DetectorConnection):
    """
    Remove a client
    """
    self.__detector_conn_list.remove(detector_conn)

  def find(self, ws_handler):
    """
    Finds client connection
    """    

    detector_conn = None
    for idx, detector_conn in enumerate(self.__detector_conn_list):
      #logger.info("Checking conn {}".format(detector_conn.id))      
      if ws_handler == detector_conn.ws_handler:
        return detector_conn
    return None

class WSMessage:
  type = None
  origin = None
  encoded = None
  content = None

  def __init__(self, type:str = None, origin: str = None, encoded: bytearray = None, content: str = None):
    self.type = type
    self.origin = origin
    self.encoded = encoded
    self.content = content
    

class WSMessageBroker():
  
  repository = None

  def __init__(self, repository=[]):
    self.repository = repository

  def treat_message(self, detector_conn_origin: DetectorConnection, msg: WSMessage):
    logger.info("Received messgae {} from {} ".format(detector_conn_origin.host, msg.content))

    if msg.type == 'detector':
      logger.info("Treating detector message")
      try:
        detector = Detector.objects.get(id=detector_conn_origin.id)
        logger.info("Identified detector as {}".format(detector.name))
      except Exception as e:
        print(str(e))
        logger.error("Detector not found")
    elif msg.type == 'user':
      logger.info("Treating user message")
    elif msg.type == 'inhibitor':
      logger.info("Treating inhibitor message")
      



class WSHandler(WebSocketHandler):

  broker = None
  connection_repository = None

  def initialize(self, connection_repository, broker):
    self.connection_repository = connection_repository
    self.broker = broker

  def open(self):
    print('new connection')
    # print(self.request.remote_ip)
    # print(self.request)
    # self.write_message("Hello World")
    pass
    
  def on_message(self, message):
    #print('message received {}'.format(message) )

    # Check whether existing connection
    detector_conn = self.connection_repository.find(self)
    if detector_conn is None:
      response = requests.get(API_USER_INFO, headers={'Authorization': message })
      if response.status_code == HTTPStatus.OK:
        # Decode message        
        payload = jwt.decode(message, verify=False)
        logger.info("Detector '{}' login ok!".format(payload['id']))
        conn = DetectorConnection(ws_handler=self, host=self.request.host, id=payload['id'])
        self.connection_repository.add( conn )
      else:
        logger.info("Detector login failed")
    else:
      logger.info("Message from detector '{}'".format(detector_conn.id) ) 

      # Decode message
      coder = DetectorCoder()
      info = coder.decode(message)      
      message = WSMessage(origin=detector_conn.id, type='detector', 
                          encoded=message, content=info)
      # Broker message
      self.broker.treat_message(detector_conn, message)



  def on_close(self):    
    detector_conn = self.connection_repository.find(self)
    logger.info("Removed detector '{}' from host {}".format(detector_conn.id, detector_conn.host))
    self.connection_repository.remove(detector_conn)


###########################
## Signal handling to avoid exception when closing
###########################
client = None
def signal_handler(sig, frame):
  logger.info('You pressed Ctrl+C!')
  logger.info('Closing WS Server ...')
  tornado.ioloop.IOLoop.instance().stop()
  logger.info('DONE!')
  sys.exit(0)

if __name__ == "__main__":

  # Configure signals
  signal.signal(signal.SIGINT, signal_handler)

  # connecting MongoEngine
  mongoengine.connect(MONGO_DB, host=MONGO_HOST, port=int(MONGO_PORT))
  logger.info("Connected MONGODB against mongodb://{}:{}/{}".format(MONGO_HOST, MONGO_PORT, MONGO_DB))

  # Create connection log object
  ConnectionLog.objects.create(type=ConnectionLog.USER, reason=ConnectionLog.CONNECTION)

  # Create web application
  connection_repository = WSConnectionReposirory()
  broker = WSMessageBroker(connection_repository)
  application = tornado.web.Application([
    (r'/api', WSHandler, dict(connection_repository=connection_repository, broker=broker)),
  ])
 

  # Starting WS Server
  logger.info("Started Data Channel WS 0.0.0.0@{}".format(WS_PORT))
  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(WS_PORT)
  tornado.ioloop.IOLoop.instance().start()

 
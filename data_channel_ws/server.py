# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asdt_api.settings")

# Python imports
import signal
import requests
from http import HTTPStatus
import jwt
import datetime

# Tornado imports
import tornado
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.websocket import WebSocketHandler

# Mongoengine connect
import mongoengine

# Project imports
from common.utils import get_logger
from common import DetectorCoder

from models import ConnectionLog
from user.models import User
from detectors.models import Detector
from inhibitors.models import Inhibitor
from groups.models import Group
from django.conf import settings

from message_broker_detection import WSRequestMessage, WSResponseMessage, WSMessageDetectionBroker

# Create logger
logger = get_logger()
logger.propagate = False


# Configuration
#API_USER_INFO = 'http://asdtdev.mooo.com/api/user/info'
#API_USER_INFO = 'http://localhost:8080/api/v3/user/info'
WS_PORT = 8081
KEEP_ALIVE_CONNECTION_PERIOD=2000 # 
LOGS_UPDATE_PERIOD=2000


class WSConnection:
  """
  Class to store info about a connection
  """
  host = None
  id = None
  type = None
  logged = False
  ws_handler = None
  msg = None
  last_msg = None

  USER = 'USER'
  DETECTOR = 'DETECTOR'
  INHIBITOR = 'INHIBITOR'

  def __init__(self, ws_handler = None, host = None, id = None, type = None):
    self.ws_handler = ws_handler
    self.host = host
    self.id = id
    self.type = type
    self.last_msg = datetime.datetime.now()
  
  def write_message(self, message):
    self.ws_handler.write_message(message)

class WSConnectionRepository:
  """
  Repository of the connections
  """

  __ws_conn_list = []

  def add(self, detector_conn: WSConnection):
    """
    Adds a client
    """
    self.send_connection_alert(detector_conn.id)
    self.__ws_conn_list.append(detector_conn)

  def remove(self, detector_conn: WSConnection):
    """
    Remove a client
    """
    self.send_disconnection_alert(detector_conn.id)
    self.__ws_conn_list.remove(detector_conn)

  def find_by_handler(self, ws_handler: WSConnection) -> WSConnection:
    """
    Finds client connection by its handler
    """    
    for idx, ws_conn in enumerate(self.__ws_conn_list):
      #logger.info("Checking conn {}".format(detector_conn.id))      
      if ws_handler == ws_conn.ws_handler:
        ws_conn.last_msg = datetime.datetime.now()
        return ws_conn
    return None

  def find_by_id(self, id: str) -> WSConnection:
    """
    Finds client connection by its handler
    """    
    for idx, ws_conn in enumerate(self.__ws_conn_list):
      #logger.info("Checking conn {} against {}".format(ws_conn.id, id))
      if id == ws_conn.id:
        return ws_conn
    return None

  def keep_alive_connection_repository(self):
    """
    Check whether connection is active
    NOTE: For me, this is a double check as WS is a persistent connection
    """
    for idx, detector_conn in enumerate(self.__ws_conn_list):
      #logger.info("Checking conn {}".format(detector_conn.id))            
      ellapsed_delta = datetime.datetime.now() - detector_conn.last_msg
      if ellapsed_delta.total_seconds() > 300:
        logger.info("Disconnecting '{}' due to inactivity".format(detector_conn.id))      
        detector_conn.close()
        self.remove(detector_conn)
        # Notify users
        self.send_disconnection_alert(detector_conn.id)


  def alert_message(self, detector_id, status) -> dict:
    return { 
      'deviceType': 'detector',
      'messageType': 'status change',
      'deviceId': detector_id,
      'data': { 'newStatus': status }
		}

  def send_connection_alert(self, detector_id):
    """
    Sends to users a detector has been connected
    """
    msg = self.alert_message(detector_id, 'connected')
    self.send_alert(msg, detector_id)


  def send_disconnection_alert(self, detector_id):
    """
    Sends to users a detector has been disconnected
    """
    msg = self.alert_message(detector_id, 'disconnected')
    self.send_alert(msg, detector_id)
    
  def send_alert(self, msg, detector_id):
    # groups related to detector
    groups_related_list = Group.objects.filter(devices__detectors__in=[detector_id])

    # Users related to detectors
    user_related_list = User.objects.filter(group__in=groups_related_list)
    user_related_list = [ str(user.id) for user in user_related_list ]

    for idx, detector_conn in enumerate(self.__ws_conn_list):
      # Check whether user is allowed
      if detector_conn.type == WSConnection.USER \
          and detector_conn.id in user_related_list:
        detector_conn.ws_handler.write_message(msg)

class WSHandler(WebSocketHandler):

  broker_detection : WSMessageDetectionBroker = None
  repository : WSConnectionRepository = None
  secret_key : str = None

  def get_model(self, type_id):
    model = None
    if type_id == WSConnection.DETECTOR:
      model = Detector
    elif type_id == WSConnection.USER:
      model = User
    elif type_id == WSConnection.INHIBITOR:
      model = Inhibitor
    return model


  def create_connection_log(self, type, id):
    """
    Shortcut functions
    """
    connection_log = ConnectionLog.objects.create(type=type, 
                                                  action=ConnectionLog.CONNECTION)
    model = self.get_model(type)
    if type == ConnectionLog.DETECTOR:    
      connection_log.detector = Detector.objects.get(id=id)
    elif type == ConnectionLog.USER: 
      connection_log.user = User.objects.get(id=id)
    elif type == ConnectionLog.INHIBITOR:
      connection_log.inhibitor = Inhibitor.objects.get(id=id)
    connection_log.save()
    
  def create_disconnection_log(self, type, id, reason):
    """
    Shortcut functions
    """
    connection_log = ConnectionLog.objects.create(type=type,
                                                  action=ConnectionLog.DISCONNECTION, 
                                                  reason=reason)
    if type == ConnectionLog.DETECTOR:    
      connection_log.detector = Detector.objects.get(id=id)
    elif type == ConnectionLog.USER: 
      connection_log.user = User.objects.get(id=id)
    elif type == ConnectionLog.INHIBITOR:
      connection_log.inhibitor = Inhibitor.objects.get(id=id)
    connection_log.save()


  def initialize(self, repository : WSConnectionRepository, 
                  broker_detection : WSMessageDetectionBroker, secret_key: str):
    self.repository = repository
    self.broker_detection = broker_detection
    self.secret_key = secret_key

  def open(self):
    # logger.info('new connection')
    # print(self.request.remote_ip)
    # print(self.request)
    # self.write_message("Hello World")
    pass

  def check_origin(self, origin):
      return True

  def on_message_register_client(self, ws_conn, message):
    """
    Treat message to register client
    """
    try:
      decoded_jwt = jwt.decode(message, self.secret_key, algorithms=['HS256'])
      instance_id = decoded_jwt['id']
      type_id = decoded_jwt['type'].upper()
      self.create_connection_log( type_id, instance_id )

      # Check if another connection for this detector and close the former
      # NOTE: For me (ST) its simpler to reject new connection
      ws_conn = self.repository.find_by_id(instance_id)
      if ws_conn is not None:
        logger.error("Logging in duplicate detector with id '{}'".format(instance_id))
        ws_conn.ws_handler.close()
        self.repository.remove(ws_conn)
        self.close()
        self.create_disconnection_log( type_id, instance_id, reason='DUPLICATED_CONNECTION' )

      # Check whether instance in DB
      # NOTE: This would be removed when logging in comes through WS
      model = self.get_model(type_id)
      if model is None:
        logger.error("Type '{}' not identified".format(type_id))
        self.close()
        return        
      # Check if exists
      if model.objects.filter(id=instance_id).count() == 0:
        logger.error("Instance type='{}' id='{}' not found".format(type_id, instance_id))
        self.create_disconnection_log( type_id, instance_id, reason='NOT_FOUND_IN_DATABASE' )


      # Append new connection to repository
      logger.info("Client type='{}' id='{}' login ok!".format(type_id, instance_id))
      ws_conn = WSConnection(ws_handler=self, host=self.request.host, 
                          id=instance_id, type=type_id.upper())
      self.repository.add( ws_conn )

      # Reply login
      self.write_message("OK")


    except Exception as e:
      logger.error("Detector token decode failed")
      logger.info("Exception " + str(e))
      self.close()
    except jwt.ExpiredSignatureError as e:
      logger.error("Detector token expired")
      logger.info("Expired " + str(e))
      self.close()

  def on_message_treat(self, ws_conn, message):
    """
    Treat a message coming from peer
    """
    logger.info("Message from peer type='{}' id='{}'".format(ws_conn.type, ws_conn.id) ) 

    # Treat message
    response_list = []
    request = WSRequestMessage(source_id=ws_conn.id, 
                                type=ws_conn.type, encoded=message)
    if request.type == WSRequestMessage.DETECTOR:
      logger.info("Treating detector message")
      response_list = self.broker_detection.treat_message_detector(request)
    elif request.type == WSRequestMessage.USER:
      logger.info("Treating user message")
    elif request.type == WSRequestMessage.INHIBITOR:
      logger.info("Treating inhibitor message")

    # NOTE: Reply to peers (myself and other indicated by response)
    for response in response_list:
      logger.info("Generating response to type={}, id={}".format(response.type, response.destination_id))
      ws_conn = self.repository.find_by_id(response.destination_id)
      if ws_conn is not None:
        ws_conn.write_message(response.content)

  def on_message(self, message):
    """
    Handler to receive message
    """
    #logger.info('message received {}'.format(message) )

    # Check whether existing connection
    ws_conn = self.repository.find_by_handler(self)        
    if ws_conn is None:
      self.on_message_register_client(ws_conn, message)
    else:
      self.on_message_treat(ws_conn, message)



  def on_close(self):    
    ws_conn = self.repository.find_by_handler(self)    
    if ws_conn is not None:
      logger.info("Closed connection. Removing type='{}' id='{}' host={}".format(ws_conn.id, ws_conn.type, ws_conn.host))
      self.repository.remove(ws_conn)



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
  mongoengine.connect(settings.MONGO_DB, host=settings.MONGO_HOST, port=int(settings.MONGO_PORT))
  logger.info("Connected MONGODB against mongodb://{}:{}/{}".format(settings.MONGO_HOST, settings.MONGO_PORT, settings.MONGO_DB))

  # Create web application
  repository = WSConnectionRepository()
  broker_detection = WSMessageDetectionBroker()
  application = tornado.web.Application([
    (r'/{}/'.format(settings.PREFIX_WS), WSHandler, dict(repository=repository, 
                              broker_detection=broker_detection, secret_key=settings.SECRET_KEY)),
  ])
 

  # Starting WS Server
  logger.info("Started Data Channel WS 0.0.0.0@{}:/{}/".format(WS_PORT,settings.PREFIX_WS))
  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(WS_PORT)

  # Checks latest activity on every connection
  PeriodicCallback(repository.keep_alive_connection_repository, 
                    KEEP_ALIVE_CONNECTION_PERIOD).start()
  PeriodicCallback(broker_detection.logs_update, 
                    LOGS_UPDATE_PERIOD).start()

  IOLoop.instance().start()

 
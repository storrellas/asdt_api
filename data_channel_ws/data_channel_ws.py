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

# Create logger
logger = get_logger()
logger.propagate = False


# Configuration
API_USER_INFO = 'http://asdtdev.mooo.com/api/user/info'
WS_PORT = 8081
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB = 'asdt'

class DetectorConnection:

  host = None
  id = None
  logged = False
  connection = None

  def __init__(self, connection = None, host = None, id = None):
    self.connection = connection
    self.host = host
    self.id = id



class WSHandler(WebSocketHandler):

  logged_in = False

  detector_conn_list = []


  def open(self):
    print('new connection')
    print(self.request.remote_ip)
    print(self.request)
    self.write_message("Hello World")
    
  def on_message(self, message):
    print('message received {}'.format(message) )

    # Finding connector
    detector_conn = None
    for idx, conn in enumerate(self.detector_conn_list):
      logger.info("Checking conn {}".format(conn.id))
      if self == conn.connection:
        detector_conn = conn

    if detector_conn is None:
      response = requests.get(API_USER_INFO, headers={'Authorization': message })
      if response.status_code == HTTPStatus.OK:
        self.logged_in == True

        # Decode message        
        payload = jwt.decode(message, verify=False)

        logger.info("Detector {} login ok!".format(payload['id']))
        conn = DetectorConnection(connection=self, host=self.request.host, id=payload['id'])
        self.detector_conn_list.append( conn )
      else:
        logger.info("Detector login failed")
    else:
      logger.info("Connection identified {}".format(detector_conn.id) ) 

      

  def on_close(self):
    print('connection closed')

application = tornado.web.Application([
  (r'/api', WSHandler),
])
 


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

  # Starting WS Server
  logger.info("Started Data Channel WS 0.0.0.0@{}".format(WS_PORT))
  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(WS_PORT)
  tornado.ioloop.IOLoop.instance().start()

 
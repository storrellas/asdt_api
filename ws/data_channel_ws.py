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
from utils import get_logger
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

class WSHandler(WebSocketHandler):

  logged_in = False

  detector_list = []

  def open(self):
    print('new connection')
    print(self.request.remote_ip)
    self.write_message("Hello World")
    
  def on_message(self, message):
    print('message received {}'.format(message) )

    if self.logged_in == False:
      response = requests.get(API_USER_INFO, headers={'Authorization': message })
      if response.status_code == HTTPStatus.OK:
        self.logged_in == True
        logger.info("Detector login ok!")
        payload = jwt.decode(message, verify=False)
        print(payload)
        print(self)
      else:
        logger.info("Detector login failed")
        print("response.status_code", response.status_code)

      

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
  http_server.listen(8081)
  tornado.ioloop.IOLoop.instance().start()
 
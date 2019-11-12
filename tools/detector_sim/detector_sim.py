import requests
import json
import sys
from http import HTTPStatus

# Project imports
from utils import get_logger

logger = get_logger()

# Configuration variables
host = 'http://asdtdev.mooo.com'
detector = '5db1b05fedd685190719f924'
password = 'test'
PORT = 80

# Session variables
token = None

def login(id, password):
  body = { 'id': id, 'password': password}
  response = requests.post(host + '/detector/authenticate', data=body)
  # Get token
  if response.status_code == HTTPStatus.OK:
    response_json = json.loads(response.content.decode()) 
    return response_json['data']['token']
  else:
    return ''
  
  print(response_json)

##############################
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen
from tornado.websocket import websocket_connect
class Client(object):
  def __init__(self, url, timeout):
    self.url = url
    self.timeout = timeout
    self.ioloop = IOLoop.instance()
    self.ws = None
    self.connect()
    PeriodicCallback(self.keep_alive, 20000).start()
    self.ioloop.start()

  @gen.coroutine
  def connect(self):
    print("trying to connect")
    try:
      self.ws = yield websocket_connect(self.url)
      self.ws.write_message( token )
    except Exception as e:
      print("connection error")
    else:
      print("connected")
      self.run()

  @gen.coroutine
  def run(self):
    while True:
      msg = yield self.ws.read_message()
      print("msg", msg)
      if msg is None:
        print("connection closed")
        self.ws = None
        break

  def keep_alive(self):
    if self.ws is None:
      self.connect()
    else:
      self.ws.write_message("keep alive")
##############################

if __name__ == "__main__":
  logger.info("Login detector with {} / {} ".format(detector, password))
  token = login(detector, password)
  if len(token) == 0:
    logger.error("Login not successful. Aborting")
    sys.exit(0)
  
  # Create websocket client
  client = Client("ws://asdtdev.mooo.com/api", 5)




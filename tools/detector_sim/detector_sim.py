import requests
import json
import sys
import random
import signal
from http import HTTPStatus

# Tornado imports
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen
from tornado.websocket import websocket_connect

# Project imports
from utils import get_logger

# Create logger
logger = get_logger()
logger.propagate = False

# Configuration variables
host = 'http://asdtdev.mooo.com'
ws_host = 'ws://asdtdev.mooo.com'
detector = '5db1b05fedd685190719f924'
password = 'test'
PORT = 80

class Client(object):
  """
  Client to connect to Websocket
  """
  token = None
  url = None
  ioloop = None
  ws = None

  def __init__(self, url, timeout):
    self.url = url
    self.timeout = timeout
    self.ioloop = IOLoop.instance()
    self.ws = None

  def login(self, id, password):
    """
    Logs detector in and stores token
    """
    body = { 'id': id, 'password': password}
    response = requests.post(host + '/detector/authenticate', data=body)
    # Get token
    if response.status_code == HTTPStatus.OK:
      response_json = json.loads(response.content.decode()) 
      self.token = response_json['data']['token']
      return True
    else:
      return False
  
  def start(self):
    """
    Start WS infinite loop
    """
    self.connect()
    PeriodicCallback(self.keep_alive, 20000).start()
    PeriodicCallback(self.send_detection, 1000).start()
    self.ioloop.start()

  @gen.coroutine
  def connect(self):    
    logger.info("Attempting to connect")
    try:
      self.ws = yield websocket_connect(self.url)
      # After connection first thing is sending token
      self.ws.write_message( self.token )
    except Exception as e:
      logger.error("connection error")
    else:
      logger.info("connected")
      self.run()

  @gen.coroutine
  def run(self):
    while True:
      msg = yield self.ws.read_message()
      logger.info("message received:{}".format(msg))
      if msg is None:
        logger.info("connection closed")
        self.ws = None
        break

  def keep_alive(self):
    if self.ws is None:
      self.connect()
    else:
      self.ws.write_message("keep alive")

  aLonAnt = 1.8
  aLatAnt = 41.7
  def send_detection(self):

    self.aLonAnt = self.aLonAnt + random.random()/100
    self.aLatAnt = self.aLatAnt + random.random()/100
    infoA = { 
      'sn': "888XIXXPXX0025", 
      'driverLocation': { 
        'lon': self.aLonAnt, 'lat': self.aLatAnt, 
        'fHeight': random.random()*10 
      },
      'droneLocation': { 
        'lon': self.aLonAnt, 'lat': self.aLatAnt, 
        'fHeight': random.random()*10 
      }, 
      'homeLocation': { 'lat': 0.0, 'lon': 0.0 }, 
      'driverLocation': { 'lat': 0.0, 'lon': 0.0 }, 
      'productId': 16 
    }
    logger.info ("Lat:{}/Lon:{}".format(self.aLatAnt, self.aLonAnt))

toDegrees = 174533.0
def encode109():
  lonAnt = 1.8
  latAnt = 41.7
  info = { 
    'sn': "888XIXXPXX0025", 
    'driverLocation': { 
      'lon': lonAnt, 'lat': latAnt, 
      'fHeight': random.random()*10 
    },
    'droneLocation': { 
      'lon': lonAnt, 'lat': latAnt, 
      'fHeight': random.random()*10 
    }, 
    'homeLocation': { 'lat': 0.0, 'lon': 0.0 }, 
    'driverLocation': { 'lat': 0.0, 'lon': 0.0 }, 
    'productId': 16 
  }

  # Declare frame
  frame = bytearray(109)
  frame[11] = 0x1F

  # 25 -> + 14 bytes [serial number] (string)
  sn_ba = bytearray(info['sn'], 'utf-8')
  #sn_ba = bytearray()
  #sn_ba.extend(map(ord, info['sn']))
  frame[25:25+len(sn_ba)] = sn_ba

  # 41 -> + 4 bytes [long drone]    
  lon = int(info['droneLocation']['lon'] * toDegrees).to_bytes(4, 'little', signed=True)
  frame[41:41+4] = lon
  # 45 -> + 4 byes [lat drone]
  lat = int(info['droneLocation']['lat'] * toDegrees).to_bytes(4, 'little', signed=True)
  frame[45:45+4] = lat

  # 49 -> + 2 bytes [absolute height] - NOTE: aHeight does not exist
  # aHeight = int(info['droneLocation']['aHeight'] * toDegrees).to_bytes(2, 'little', signed=True)
  # frame[49:49+2] = aHeight
  # 51 -> + 2 bytes [floor height]
  fHeight = int(info['droneLocation']['fHeight'] * 10).to_bytes(2, 'little', signed=True)
  frame[51:51+2] = fHeight

  # NOTE: WATCH OUT THIS ONE IS LAT first, LON second
  # 69 -> + 4 bytes [lat driver] 
  lat = int(info['driverLocation']['lat'] * toDegrees).to_bytes(4, 'little', signed=True)
  frame[69:69+4] = lat
  # 73 -> + 4 bytes [lon driver]
  lon = int(info['driverLocation']['lon'] * toDegrees).to_bytes(4, 'little', signed=True)
  frame[73:73+4] = lon

  # 77 -> + 4 bytes [lon home]
  lon = int(info['homeLocation']['lon'] * toDegrees).to_bytes(4, 'little', signed=True)
  frame[77:77+4] = lon
  # 81 -> + 4 bytes [lat home]
  lat = int(info['homeLocation']['lat'] * toDegrees).to_bytes(4, 'little', signed=True)
  frame[81:81+4] = lat

  # 85 -> + 1 byte [product type]
  productId = int(info['productId']).to_bytes(1, 'little', signed=False)
  frame[85:85] = productId



  print(type(sn_ba))
  print(type(frame))

  #
  #frame[3] = 0xA2
  print(sn_ba)
  print(frame)
  print("-- After --")
  print(lon)
  print(frame[41:45])
  print(lat)
  print(frame[45:49])
  print(frame[85])

  print(len(frame))





###########################
## Signal handling to avoid exception when closing
###########################
client = None
def signal_handler(sig, frame):
  logger.info('You pressed Ctrl+C!')
  logger.info('Closing WS Connection ...')
  client.ws.close()
  logger.info('DONE!')
  sys.exit(0)

if __name__ == "__main__":
  encode109()



  """
  logger.info("Login detector with ({}/{})".format(detector, password))
  signal.signal(signal.SIGINT, signal_handler)

  # Create websocket client
  client = Client(ws_host + "/api", 5)
  result = client.login(detector, password)
  if not result:
    logger.error("Login Failed. Aborting")
    sys.exit(0)
  # Infinite loop
  client.start()
  """






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

# GPX Export
import gpx_parser
from gpx_parser.GPXTrackSegment import GPXTrackSegment
from gpx_parser.GPXTrackPoint import GPXTrackPoint
from gpx_parser.GPXTrack import GPXTrack

# Project imports
from utils import get_logger

# Create logger
logger = get_logger()
logger.propagate = False

# # Configuration variables
# host = 'http://asdtdev.mooo.com'
# ws_host = 'ws://asdtdev.mooo.com'
# detector = '5db1b05fedd685190719f924'
# password = 'test'
# # host = 'http://localhost:8080'
# # ws_host = 'ws://localhost:8080'
# # detector = '5dcafabcb6da1533e91e377d'
# # password = 'Asdt2019.'

from detector_sim_config import *

class DetectorWSClient(object):
  """
  Client to connect to Websocket simulating logs generated 
  by detector localising drones
  """
  token = None
  url = None
  ioloop = None
  ws = None

  # Drone status
  sn = None
  lat = None
  lon = None
  __toDegrees = 174533.0

  # GPX output
  gpx = None

  def __init__(self, url, sn, lat_ini, lon_ini, timeout):
    self.url = url
    self.timeout = timeout

    # Drone detected configuration
    self.sn = sn
    self.lat = lat_ini
    self.lon = lon_ini

    # Generate output for GPX
    gpx_track_segment = GPXTrackSegment()    
    gpx_track = GPXTrack(name=self.sn, segments=[gpx_track_segment])
    self.gpx = gpx_parser.GPX(version="1.0", creator="detector_sim", tracks=[gpx_track])

    
  def login(self, id, password):
    """
    Logs detector in and stores token
    """
    body = { 'id': id, 'password': password }
    response = requests.post(HOST + '/detector/authenticate', data=body)
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
    #PeriodicCallback(self.keep_alive, 20000).start()
    PeriodicCallback(self.send_detection, 2000).start()
    
    # Create IOLoop
    self.ioloop = IOLoop.instance()
    
    self.ioloop.spawn_callback(self.connect)

    # # Runs single task
    # self.ioloop.run_sync(self.connect)

    print("Starting IOLoop")
    self.ioloop.start()

  # NOTE: This is kept here for reference
  # @gen.coroutine
  # def connect(self):    
  #   logger.info("Attempting to connect")
  #   try:
  #     self.ws = yield websocket_connect(self.url)
  #     # After connection first thing is sending token
  #     self.ws.write_message( self.token )
  #   except Exception as e:
  #     logger.error("connection error")
  #   else:
  #     logger.info("connected")
  #     self.run()

  # @gen.coroutine
  # def run(self):
  #   while True:
  #     msg = yield self.ws.read_message()
  #     logger.info("message received:{}".format(msg))
  #     if msg is None:
  #       logger.info("connection closed")
  #       self.ws = None
  #       break

  async def connect(self):    
    logger.info("Attempting to connect")
    try:
      self.ws = await websocket_connect(self.url)
      # After connection first thing is sending token
      self.ws.write_message( self.token )
    except Exception as e:
      logger.error("connection error")
    else:
      logger.info("connected")
      await self.run()

  async def run(self):
    while True:
      msg = await self.ws.read_message()
      logger.info("message received:{}".format(msg))
      if msg is None:
        logger.info("connection closed")
        self.ws = None
        break

  # def keep_alive(self):
  #   if self.ws is None:
  #     self.connect()
  #   else:
  #     self.ws.write_message("keep alive")


  def send_detection(self):
    """
    Generates the package sent by the detector via WS
    """
    
    # Calculate new position
    self.lat = self.lat + random.random()/100
    self.lon = self.lon + random.random()/100

    # Generate package
    info = { 
      'sn': self.sn, 
      'driverLocation': { 
        'lat': self.lat, 'lon': self.lon,
        'fHeight': random.random()*10 
      },
      'droneLocation': { 
        'lat': self.lat, 'lon': self.lon,  
        'fHeight': random.random()*10 
      }, 
      'homeLocation': { 'lat': 0.0, 'lon': 0.0 }, 
      'driverLocation': { 'lat': 0.0, 'lon': 0.0 }, 
      'productId': 16 
    }
    logger.info ("Sending detection -> SN:{}/Lat:{}/Lon:{}".format(self.sn, self.lat, self.lon))

    # Output GPX file
    self._gpx_output(self.lat, self.lon)

    # Encode package
    frame = self._encode109(info)    
    self.ws.write_message(bytes(frame), binary=True)

  def _gpx_output(self, lat, lon):
    self.gpx.tracks[0].segments[0].append( GPXTrackPoint(lat=str(lat),lon=str(lon)) )
    filename = self.sn + '.gpx'
    with open(filename, 'w') as output_file:
      output_file.write(self.gpx.to_xml())

  def _encode109(self, info):

    # Declare frame
    frame = bytearray(109)
    frame[11] = 0x1F

    # 25 -> + 14 bytes [serial number] (string)
    sn_ba = bytearray(info['sn'], 'utf-8')
    #sn_ba = bytearray()
    #sn_ba.extend(map(ord, info['sn']))
    frame[25:25+len(sn_ba)] = sn_ba

    # 41 -> + 4 bytes [long drone]    
    lon = int(info['droneLocation']['lon'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[41:41+4] = lon
    # 45 -> + 4 byes [lat drone]
    lat = int(info['droneLocation']['lat'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[45:45+4] = lat

    # 49 -> + 2 bytes [absolute height] - NOTE: aHeight does not exist
    # aHeight = int(info['droneLocation']['aHeight'] * __toDegrees).to_bytes(2, 'little', signed=True)
    # frame[49:49+2] = aHeight
    # 51 -> + 2 bytes [floor height]
    fHeight = int(info['droneLocation']['fHeight'] * 10).to_bytes(2, 'little', signed=True)
    frame[51:51+2] = fHeight

    # NOTE: WATCH OUT THIS ONE IS LAT first, LON second
    # 69 -> + 4 bytes [lat driver] 
    lat = int(info['driverLocation']['lat'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[69:69+4] = lat
    # 73 -> + 4 bytes [lon driver]
    lon = int(info['driverLocation']['lon'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[73:73+4] = lon

    # 77 -> + 4 bytes [lon home]
    lon = int(info['homeLocation']['lon'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[77:77+4] = lon
    # 81 -> + 4 bytes [lat home]
    lat = int(info['homeLocation']['lat'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[81:81+4] = lat

    # 85 -> + 1 byte [product type]
    productId = int(info['productId']).to_bytes(1, 'little', signed=False)
    frame[85:85] = productId

    #print(frame)
    return frame





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

  # Configure signals
  signal.signal(signal.SIGINT, signal_handler)

  # Create websocket client
  lat = 41.7
  lon = 1.8
  sn = "888XIXXPXX0025"
  client = DetectorWSClient(WS_HOST + "/api", sn, lat, lon, 5)    
  logger.info("Login detector with ({}/{})".format(DETECTOR, PASSWORD))
  result = client.login(DETECTOR, PASSWORD)
  if not result:
    logger.error("Login Failed. Aborting")
    sys.exit(0)
  # Infinite loop
  client.start()
  






# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Python imports
import requests
import json
import sys
import random
import signal
import os
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
from common.utils import get_logger

# Create logger
logger = get_logger()
logger.propagate = False

# Loads configuration
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

  # Detector
  id = None

  # Drone status
  sn = None
  lat = None
  lon = None
  __toDegrees = 174533.0

  # GPX output
  output_gpx = None
  input_gpx = None

  def __init__(self, url, sn, lat_ini, lon_ini, timeout, gpx_file):
    self.url = url
    self.timeout = timeout

    # Drone detected configuration
    self.sn = sn
    self.lat = lat_ini
    self.lon = lon_ini

    # Generate output for GPX
    gpx_track = GPXTrack(name=self.sn)
    self.output_gpx = gpx_parser.GPX(version="1.0", creator="detector_sim", tracks=[gpx_track])

    # Load gpx if any
    if gpx_file is not None:
      with open(gpx_file, 'r') as gpx_fd:
        self.input_gpx = gpx_parser.parse(gpx_fd)
        logger.info("{} tracks loaded".format(len(self.input_gpx)))


    
  def login(self, id, password):
    """
    Logs detector in and stores token
    """
    self.id = id
    body = { 'id': id, 'password': password }
    print("body", body)
    response = requests.post(API_AUTH, data=body)
    # Get token
    if response.status_code == HTTPStatus.OK:
      response_json = json.loads(response.content.decode()) 
      print(response_json)
      if response_json['success']:
        self.token = response_json['data']['token']
        return True      
    return False
    
    # # Hacking
    # self.token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiZGV0ZWN0b3IiLCJpZCI6IjVkYjFiMDVmZWRkNjg1MTkwNzE5ZjkyNCIsImlhdCI6MTU3NDI1NDU3MywiZXhwIjoxNTc0Mjc2MTczLCJpc3MiOiJBU0RUIn0.XCjIUaCQIbZRGyB9T4UAXkolTCcRVEnWMzhcHLCOYppsB4KfFrkTc5rQEktw_Tc26pXh868PjxrZ4uZGTW7q8Q'
    # return True


  def configure_ioloop(self):
    """
    Configures ioloop to be running
    """
    #PeriodicCallback(self.keep_alive, 20000).start()
    PeriodicCallback(self.send_detection, self.timeout).start()
    
    # Create IOLoop
    self.ioloop = IOLoop.instance()
    
    # Add to the ioloop 
    self.ioloop.spawn_callback(self.connect)

    # # Runs single task
    # self.ioloop.run_sync(self.connect)

    # print("Starting IOLoop")
    # self.ioloop.start()

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
    try:
      self.ws = await websocket_connect(self.url)
      # After connection first thing is sending token
      self.ws.write_message( self.token )
    except Exception as e:
      logger.error("connection error")
    else:
      logger.info("Detector '{}' connected".format(self.id))
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

  current_segment = 0

  def send_detection(self):
    """
    Generates the package sent by the detector via WS
    """
    
    if self.input_gpx is None:
      # Calculate new position
      self.lat = self.lat + random.random()/100
      self.lon = self.lon + random.random()/100
    else:
      #logger.info("Loading new position from from GPX File")
      gpx_track_segment = self.input_gpx[0].segments[self.current_segment]
      gps_track_point = gpx_track_segment[0]
      # print(gps_track_point)
      # print(gps_track_point.lat)
      self.lat = gps_track_point.latitude
      self.lon = gps_track_point.longitude
      # Check for next segment
      self.current_segment = self.current_segment + 1
      if self.current_segment >= len(self.input_gpx[0].segments):
        self.current_segment = 0

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
    logger.info ("SimulatingDetection - SN:{}/Lat:{}/Lon:{}".format(self.sn, self.lat, self.lon))

    # Output GPX file
    self._gpx_output(self.lat, self.lon)

    # Encode package
    frame = self._encode109(info)    
    self.ws.write_message(bytes(frame), binary=True)

  def _gpx_output(self, lat, lon):
    # A Track Segment holds a list of Track Points which are logically connected in order. 
    # To represent a single GPS track where GPS reception was lost, or the GPS receiver was turned off, 
    # start a new Track Segment for each continuous span of track data.
    # See: http://www.topografix.com/GPX/1/1/#type_trksegType
    
    # Append point
    gpx_track_segment = GPXTrackSegment(points=[GPXTrackPoint(lat=str(lat),lon=str(lon))] )
    self.output_gpx.tracks[0].segments.append(gpx_track_segment)

    # Output to file
    filename = self.sn + '.gpx'
    with open(OUTPUT_PATH + '/' + filename, 'w') as output_file:
      output_file.write(self.output_gpx.to_xml())

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


import argparse


if __name__ == "__main__":
  print("MyPython")

  # Configure argparse
  parser = argparse.ArgumentParser(description='Detector sim arguments')
  parser.add_argument("--detector", default=None, help="detector")
  parser.add_argument("--password", default=None, help="password")

  # Parse arguments if any
  args = parser.parse_args()
  detector_id = args.detector if args.detector is not None else DETECTOR
  password = args.password if args.password is not None else PASSWORD

  # Configure signals
  signal.signal(signal.SIGINT, signal_handler)

  if not os.path.exists(OUTPUT_PATH):
      os.makedirs(OUTPUT_PATH)
  
  # Looping to create multiple detectors
  for detector in DETECTOR_LIST:
    logger.info("Launching detector {} with timeout {}".format(detector['sn'], detector['timeout']))
    client = DetectorWSClient(WS_HOST, detector['sn'], 
                              detector['lat'], detector['lon'], detector['timeout'], detector['gpx'])    
    # Login detector
    logger.info("Login detector with ({}/{})".format(DETECTOR, PASSWORD))
    result = client.login(detector_id, password)
    if not result:
      logger.error("Login Failed. Aborting")
      sys.exit(0)
    # Infinite loop
    client.configure_ioloop()

  
  # Create IOLoop
  ioloop = IOLoop.instance()
  logger.info("Starting IOLoop")
  ioloop.start()
  






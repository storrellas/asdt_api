# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)


# Python
import argparse
import requests
import json
import sys
import random
import signal
import os
import datetime
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
from common import DetectorCoder, LogMessage, LogLocationMessage

# Create logger
logger = get_logger()
logger.propagate = False

# Configuration parameters
# WS_URL = 'ws://localhost:8081/ws/v3/'
# API_URL = 'http://localhost:8080'

WS_URL = 'wss://asdtdev.mooo.com/api/'
API_URL = 'https://asdtdev.mooo.com'

OUTPUT_PATH = './output'

class DroneFlight:

  sn = None
  lat = None
  lon = None
  input_gpx = None
  output_gpx = None
  timeout = None
  current_segment = 0
  output_gpx_enable = False
  last_detection_timestamp = None

  # Count number of detections
  current_detection = 0
  max_detection = 0
  
  def __init__(self, sn, lat, lon, timeout = 0, gpx_file = None):
    self.sn = sn
    self.lat = lat
    self.lon = lon
    self.timeout = timeout
    self.last_detection_timestamp = datetime.datetime.now()

    # Generate output path
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    # Generate output for GPX
    gpx_track = GPXTrack(name=self.sn)
    self.output_gpx = gpx_parser.GPX(version="1.0", creator="detector_sim", tracks=[gpx_track])

    # Load gpx if any
    if gpx_file is not None:
      with open(gpx_file, 'r') as gpx_fd:
        self.input_gpx = gpx_parser.parse(gpx_fd)
        logger.info("{} tracks loaded".format(len(self.input_gpx)))

  def get_detection_log(self):
    # Configuration of maximum number of detections
    if self.max_detection > 0:
      if self.current_detection >= self.max_detection:
        logger.info("Reached max number of segments/detections")
        return
    self.current_detection = self.current_detection + 1

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
    driverLocation = LogLocationMessage(lat=self.lat, lon=self.lon, fHeight=random.random()*10)
    droneLocation = LogLocationMessage(lat=self.lat, lon=self.lon, fHeight=random.random()*10)
    homeLocation = LogLocationMessage(lat=self.lat, lon=self.lon)
    log = LogMessage(sn=self.sn, driverLocation=driverLocation,
                      droneLocation=droneLocation, homeLocation=homeLocation,
                      productId=16)
    logger.info ("Detection[{}] - SN:{}/Lat:{}/Lon:{}" \
                    .format(self.current_detection, self.sn, self.lat, self.lon))
    
    # Output GPX file
    if self.output_gpx_enable:
      self._gpx_output(log.droneLocation.lat, log.droneLocation.lon)

    return log

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

class WSClient:
  # WS Management
  token = None
  ws_url = None
  ioloop = None
  ws = None
  ws_connected = False

  # Instance Type
  name = 'Undefined'
  id = None

  def __init__(self, ws_url = None, id = None):
    self.ws_url = ws_url
    self.id = id

  def is_ws_connected(self):
    return self.ws_connected
  
  def set_ws_connected(self, ws_connected):
    self.ws_connected = ws_connected

  def login(self, url, body):
    # Capture id from body
    if 'id' in body:
      self.id = body['id']
    elif 'email' in body:
      self.id = body['email']
    else:
      self.id = 'unknown'

    logger.info("Authenticating HTTP {}".format(url))
    response = requests.post(url, data=body)
    #print(response.content)
    # Get token
    if response.status_code == HTTPStatus.OK:
      response_json = json.loads(response.content.decode()) 

      # API /v1/ and /v2/ API versions
      if 'success' in response_json:
        if response_json['success']:
          self.token = response_json['data']['token']
          return (True, self.token)
      else:
        # API v3
        self.token = response_json['token']
        return (True, self.token)
    return (False, self.token)
    
    # Hacking - Remote token
    # self.token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0eXBlIjoidXNlciIsImlkIjoiNWRkZDViNDllNDc4YTExMTY2YWM5ODRlIiwiaXNzIjoiQVNEVCIsImlhdCI6MTU3NDkzMTA5NCwiZXhwIjoxNTc0OTUyNjk0fQ.y0TM4AH98imjninAYEps73LSibiM3THpS2urcNcVJNQ'
    # return (True, self.token)

    # # Hacking - Local token
    # self.token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0eXBlIjoidXNlciIsImlkIjoiNWRkYThjN2VmMTYxYTRiZGQwNWY5OGUxIiwiaXNzIjoiQVNEVCIsImlhdCI6MTU3NDkyMjk3NSwiZXhwIjoxNTc0OTQ0NTc1fQ.87miRUY_qy4WzC-zKe6kXYdDTkKKG0BOFMPWca9kdEs'
    # return (True, self.token)

  async def connect(self):    
    try:
      logger.info("Connection WS {}".format(self.ws_url))
      #self.ws = await websocket_connect(self.ws_url)
      self.ws = await websocket_connect(self.ws_url, on_message_callback=self.on_message_callback)
      # After connection first thing is sending token
      self.ws.write_message( self.token )
    except Exception as e:
      print(str(e))
      logger.error("connection error")
      self.set_ws_connected( False )
    else:
      logger.info("{} '{}' connected".format(self.name, self.id))
      self.set_ws_connected( True )
      # NOTE: This makes it blocking
      #await self.run()
      #IOLoop.instance().spawn_callback(self.run)

  def on_message_callback(self, msg):
    logger.info("message received:{}".format(msg))
    if msg is None:
      self.set_ws_connected( False )
      logger.info("connection closed {} id={}".format( self.is_ws_connected(), self.id ) )
      # Close if its not done
      if self.ws is not None:
        self.close()
      self.ws = None

  # async def run(self):
  #   print("Running")
  #   while True:
  #     msg = await self.ws.read_message()
  #     logger.info("message received:{}".format(msg))
  #     if msg is None:
  #       logger.info("connection closed")
  #       self.ws = None
  #       break

  # def keep_alive(self):
  #   if self.ws is None:
  #     self.connect()
  #   else:
  #     self.ws.write_message("keep alive")

  def close(self):
    """
    Closes client
    """
    # Encode package
    logger.info("Closing connection")
    if self.ws is not None:
      self.ws.close()
    self.ws = None
    self.set_ws_connected( False )

class WSDetectorClient(WSClient):
  """
  Client to connect to Websocket simulating logs generated 
  by detector localising drones
  """
  # Instance type
  id = None
  name = 'Detector'

  # Drone flight configuration
  drone_flight_list = None

  def __init__(self, ws_url = None, id = None, drone_flight_list = None):
    super().__init__(ws_url, id)
   
    # Drone detected configuration
    self.drone_flight_list = drone_flight_list
    

  def send_detection_log_periodic(self):
    """
    Generates the package sent by the detector via WS
    """
    # Generate next detection log
    for drone_flight in self.drone_flight_list:
      now = datetime.datetime.now()
      if (now - drone_flight.last_detection_timestamp).total_seconds() * 1000 > drone_flight.timeout:
        detection_log = drone_flight.get_detection_log()
        # Send detection
        self.send_detection_log(detection_log)
        drone_flight.last_detection_timestamp = now

  def send_detection_log(self, detection_log):
    """
    Generates the package sent by the detector via WS
    """
    # Encode package
    coder = DetectorCoder()
    frame = coder.encode(detection_log)    
    if self.is_ws_connected():
      self.ws.write_message(bytes(frame), binary=True)
    else:
      logger.error("Failed to send to client")

# END: WSDetectorClient

class WSUserClient(WSClient):
  """
  Client to connect to Websocket simulating logs generated 
  by detector localising drones
  """

  name = 'User'
  message_list = []

  def on_message_callback(self, msg):
    logger.info("Added message to received list")
    self.message_list.append( msg )
    super().on_message_callback( msg )


# END: WSUserClient


def read_json_configuration(filename):
  # Configuration parameters
  config = {}
  try:
      with open(filename) as json_file:
        config = json.load(json_file)
        return config
  except FileNotFoundError:
      logger.error("Config file not found")
      sys.exit(0)



###########################
## Signal handling to avoid exception when closing
###########################
client_list = []
periodic_callback = None
def signal_handler(sig, frame):
  logger.info('You pressed Ctrl+C!')
  logger.info('Closing WS Connection ...')
  for client in client_list:
    client.close()
  logger.info('DONE!')
  sys.exit(0)

def send_detection_log_periodic_list():
  global periodic_callback
  for client in client_list:
    if client.is_ws_connected() == False:
      logger.error("Client {} id={} is closed. Aborting".format(client.name, client.id) )
      periodic_callback.stop()
      sys.exit(0)
    client.send_detection_log_periodic()

def generate_drone_flight_list(config):
  """
  Generates drone flight list from configuration
  """
  drone_flight_list = []
  for idx, drone_flight in enumerate(config['detector_list'][0]['drone_flight_list']):
    logger.info("Launching drone flight {} with timeout {}" \
                  .format(drone_flight['sn'], drone_flight['timeout']))
    drone_flight = DroneFlight(drone_flight['sn'], 
                                drone_flight['lat'], drone_flight['lon'], 
                                drone_flight['timeout'], drone_flight['gpx'])
    drone_flight.output_gpx_enable = True
    drone_flight_list.append(drone_flight)

  return drone_flight_list

if __name__ == "__main__":

  # Configure signals
  signal.signal(signal.SIGINT, signal_handler)

  # Configure argparse
  parser = argparse.ArgumentParser(description='Detector sim arguments')
  parser.add_argument("--config", default=None, help="config file path")

  # Parse arguments if any
  args = parser.parse_args()
  config_filename = args.config if args.config is not None else './config.json'

  
  # Read configuration
  logger.info("Loading configuration from '{}' ".format(config_filename))
  config = read_json_configuration( config_filename )

  ## LAUCHING DETECTORS
  #####################
  for detector in config['detector_list']:
    # Get credentials
    # NOTE: We should make this to be multi drone
    detector_id = detector['id']
    password = detector['password']

    # Create client
    drone_flight_list = generate_drone_flight_list(config)
    client = WSDetectorClient(WS_URL, detector_id, drone_flight_list)    
    # Login detector
    logger.info("Login detector with ({}/{})".format(detector_id, password))
    body = { 'id': detector_id, 'password': password }
    result, token = client.login('{}/api/v3/detectors/authenticate/'.format(API_URL), body)
    if not result:
      logger.error("Login Failed. Aborting")
      sys.exit(0)
      
    # Add client to list
    client_list.append(client)
    
    # Add to the ioloop 
    IOLoop.instance().spawn_callback(client.connect)

  ## LAUCHING USERS
  #####################
  for user in config['user_list']:
    # Get credentials
    # NOTE: We should make this to be multi drone
    email = user['email']
    password = user['password']

    # Create client
    client = WSUserClient(WS_URL, email)    
    # Login detector
    logger.info("Login user with ({}/{})".format(email, password))
    body = { 'email': email, 'password': password }
    result, token = client.login('{}/api/v3/user/authenticate/'.format(API_URL), body)
    if not result:
      logger.error("Login Failed. Aborting")
      sys.exit(0)
    
    # Add client to list
    client_list.append(client)

    # Add to the ioloop 
    IOLoop.instance().spawn_callback(client.connect)


  # Configure IOLoop
  periodic_callback = PeriodicCallback(send_detection_log_periodic_list, 10)
  periodic_callback.start()

  # Create IOLoop
  ioloop = IOLoop.instance()
  logger.info("Starting IOLoop")
  ioloop.start()
  






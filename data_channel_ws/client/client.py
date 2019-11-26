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
WS_URL = 'ws://localhost:8081/api'
API_AUTH_URL = 'http://localhost:8080/api/v3/detectors/authenticate/'
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

  # Count number of detections
  current_detection = 0
  max_detection = 0
  
  def __init__(self, sn, lat, lon, timeout = 0, gpx_file = None):
    self.sn = sn
    self.lat = lat
    self.lon = lon
    self.timeout = timeout

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

class DetectorWSClient:
  """
  Client to connect to Websocket simulating logs generated 
  by detector localising drones
  """
  token = None
  ws_url = None
  ioloop = None
  ws = None
  ws_connected = False

  # Detector
  id = None

  # Drone flight configuration
  drone_flight = None

  def __init__(self, ws_url = None, drone_flight = None):
    self.ws_url = ws_url
   
    # Drone detected configuration
    self.drone_flight = drone_flight
  
  @staticmethod
  def login_request(url, id, password):
    """
    Logs detector in and stores token
    """
    body = { 'id': id, 'password': password }
    logger.info("Authenticating HTTP {}".format(url))
    response = requests.post(url, data=body)
    #print(response.content)
    # Get token
    if response.status_code == HTTPStatus.OK:
      response_json = json.loads(response.content.decode()) 

      # API /v1/ and /v2/ API versions
      if 'success' in response_json:
        if response_json['success']:
          token = response_json['data']['token']
          return True      
      else:
        # API v3
        token = response_json['token']
        return (True, token)
    return (False, None)
    
    # # Hacking
    # self.token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiZGV0ZWN0b3IiLCJpZCI6IjVkYjFiMDVmZWRkNjg1MTkwNzE5ZjkyNCIsImlhdCI6MTU3NDI1NDU3MywiZXhwIjoxNTc0Mjc2MTczLCJpc3MiOiJBU0RUIn0.XCjIUaCQIbZRGyB9T4UAXkolTCcRVEnWMzhcHLCOYppsB4KfFrkTc5rQEktw_Tc26pXh868PjxrZ4uZGTW7q8Q'
    # return True

  def login(self, url, id, password):
    self.id = id    
    (result, token) =  DetectorWSClient.login_request(url, id, password)
    self.token = token
    return (result, token)

  def is_ws_connected(self):
    return self.ws_connected

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
      self.ws_connected = False
    else:
      logger.info("Detector '{}' connected".format(self.id))
      self.ws_connected = True
      # NOTE: This makes it blocking
      #await self.run()
      #IOLoop.instance().spawn_callback(self.run)

  def on_message_callback(self, msg):
    logger.info("message received:{}".format(msg))
    if msg is None:
      self.ws_connected = False
      logger.info("connection closed {}".format(self.ws_connected))
      # Close if its not done
      if self.ws is not None:
        self.ws.close()
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


  def send_detection_log_periodic(self):
    """
    Generates the package sent by the detector via WS
    """
    # Generate next detection log
    detection_log = self.drone_flight.get_detection_log()
    # Send detection
    self.send_detection_log(detection_log)

  def send_detection_log(self, detection_log):
    """
    Generates the package sent by the detector via WS
    """
    # Encode package
    coder = DetectorCoder()
    frame = coder.encode(detection_log)    
    self.ws.write_message(bytes(frame), binary=True)

  def close(self):
    """
    Closes client
    """
    # Encode package
    self.ws.close()
    self.ws = None
    self.ws_connected = False

# END: DetectorWSClient


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

  # Configure argparse
  parser = argparse.ArgumentParser(description='Detector sim arguments')
  parser.add_argument("--config", default=None, help="config file path")

  # Parse arguments if any
  args = parser.parse_args()
  config_filename = args.config if args.config is not None else './config.json'

  
  # Read configuration
  config = read_json_configuration('./config.json')

  # Get credentials
  # NOTE: We should make this to be multi drone
  detector_id = config['detector_list'][0]['id']
  detector_password = config['detector_list'][0]['password']

  
  # Looping to create multiple detectors
  for drone_flight_conf in config['detector_list'][0]['drone_flight_list']:

    # Create drone_flight
    logger.info("Launching drone flight {} with timeout {}" \
                  .format(drone_flight_conf['sn'], drone_flight_conf['timeout']))
    drone_flight = DroneFlight(drone_flight_conf['sn'], 
                                drone_flight_conf['lat'], drone_flight_conf['lon'], 
                                drone_flight_conf['timeout'], drone_flight_conf['gpx'])
    drone_flight.output_gpx_enable = True                                
    client = DetectorWSClient(WS_URL, drone_flight)    
    # Login detector
    logger.info("Login detector with ({}/{})".format(detector_id, detector_password))
    result, token = client.login(API_AUTH_URL, detector_id, detector_password)
    if not result:
      logger.error("Login Failed. Aborting")
      sys.exit(0)
    
    # Configure IOLoop
    if drone_flight.timeout > 0:
      logger.info("Launching periodic task")
      PeriodicCallback(client.send_detection_log_periodic, drone_flight.timeout).start()
   
    # Add to the ioloop 
    IOLoop.instance().spawn_callback(client.connect)
    # IOLoop.instance().run_sync(client.connect)
    # if client.is_ws_connected():
    #   logger.info("Client connected successfully")
    #   IOLoop.instance().spawn_callback(client.run)



  
  # Create IOLoop
  ioloop = IOLoop.instance()
  logger.info("Starting IOLoop")
  ioloop.start()
  






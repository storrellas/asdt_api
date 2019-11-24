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
API_AUTH = 'http://localhost:8080/api/v3/detectors/authenticate/'
WS_HOST = 'ws://localhost:8081/api'
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
  
  def __init__(self, sn, lat, lon, timeout, gpx_file):
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
  url = None
  ioloop = None
  ws = None

  # Detector
  id = None

  # Drone flight configuration
  drone_flight = None

  def __init__(self, url, drone_flight):
    self.url = url
   
    # Drone detected configuration
    self.drone_flight = drone_flight
    
  def login(self, id, password):
    """
    Logs detector in and stores token
    """
    self.id = id
    body = { 'id': id, 'password': password }
    logger.info("Authenticating HTTP {}".format(API_AUTH))
    response = requests.post(API_AUTH, data=body)
    #print(response.content)
    # Get token
    if response.status_code == HTTPStatus.OK:
      response_json = json.loads(response.content.decode()) 

      # API /v1/ and /v2/ API versions
      if 'success' in response_json:
        if response_json['success']:
          self.token = response_json['data']['token']
          return True      
      else:
        # API v3
        self.token = response_json['token']
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
    PeriodicCallback(self.send_detection, self.drone_flight.timeout).start()
    
    # Create IOLoop
    self.ioloop = IOLoop.instance()
    
    # Add to the ioloop 
    self.ioloop.spawn_callback(self.connect)

    # # Runs single task
    # self.ioloop.run_sync(self.connect)

    # print("Starting IOLoop")
    # self.ioloop.start()

  async def connect(self):
    try:
      logger.info("Connection WS {}".format(self.url))
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


  def send_detection(self):
    """
    Generates the package sent by the detector via WS
    """
    # Generate next detection log
    log = self.drone_flight.get_detection_log()

    # Encode package
    coder = DetectorCoder()
    frame = coder.encode(log)    
    self.ws.write_message(bytes(frame), binary=True)

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
    client = DetectorWSClient(WS_HOST, drone_flight)    
    # Login detector
    logger.info("Login detector with ({}/{})".format(detector_id, detector_password))
    result = client.login(detector_id, detector_password)
    if not result:
      logger.error("Login Failed. Aborting")
      sys.exit(0)
    # Infinite loop
    client.configure_ioloop()

  
  # Create IOLoop
  ioloop = IOLoop.instance()
  logger.info("Starting IOLoop")
  ioloop.start()
  






# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Python imports
import copy
import signal
import json
import requests
from http import HTTPStatus
import jwt
import datetime
from geopy.distance import geodesic

# Mongoengine connect
import mongoengine

# Project imports
from common.utils import get_logger
from common import DetectorCoder, LogMessage, LogLocationMessage

from models import ConnectionLog
from user.models import User
from detectors.models import Detector
from inhibitors.models import Inhibitor
from groups.models import Group
from drones.models import DroneModel, Drone
from logs.models import Log

# Create logger
logger = get_logger()
logger.propagate = False

class LogStorageDataMessage(LogMessage):
  dateIni = datetime.datetime.now()
  dateFin = datetime.datetime.now()
  # Coming from detector
  sn = None
  # Matching with Drone if any
  detectors = []
  model = None
  owner = None
  productId = None

  # Calculated fields
  maxHeight = None
  distanceTraveled = None
  distanceToDetector = 0

  # Adding successive items
  route = []

class LogStorageMessage:
  lastUpdate = datetime.datetime.now()
  detectors = []
  lastDetector = None
  sendInfo = False
  msgCount = 0
  data = LogStorageDataMessage()

  def __init__(self, ):
    self.data.distanceTraveled = 0

  def update(self):
    self.lastUpdate = datetime.datetime.now()


class WSMessage:
  USER = 'USER'
  DETECTOR = 'DETECTOR'
  INHIBITOR = 'INHIBITOR'

class WSRequestMessage(WSMessage):
  type = None
  source_id = None
  encoded = None
  content = None

  def __init__(self, type:str = None, source_id: str = None, encoded: bytearray = None, content: str = None):
    self.type = type
    self.source_id = source_id
    self.encoded = encoded
    self.content = content

class WSResponseMessage(WSMessage):
  type = None
  destination_id = None
  encoded = None
  content = None

  def __init__(self, type:str = None, destination_id: str = None, 
                encoded: bytearray = None, content: str = None):
    self.type = type
    self.destination_id = destination_id
    self.encoded = encoded
    self.content = content



class WSMessageBroker:
  
  # repository = LogMessageRepository()
  __log_message_dict = {}

  # Maximum time without detections to consider a flight is finished
  maxElapsedTime = 5000

  def logs_update(self):
    """
    Update logs in DB
    NOTE: We should move this to the former
    """
    for sn in self.__log_message_dict.keys():
      log_message = self.__log_message_dict[sn]
      now = datetime.datetime.now()
      delta_time = now - log_message.lastUpdate
      if delta_time.total_seconds() * 1000 > self.maxElapsedTime:
        logger.info("Saving logs automatically as considering flight as finished {}" .format(delta_time.total_seconds() * 1000))

        
  def save_log(self, log_storage):
    logger.info("Saving log to DB")

    # Seeking for Log
    dateFinLower = log_storage.data.dateFin - datetime.timedelta(minutes=10)
    dateFinHigher = log_storage.data.dateFin + datetime.timedelta(minutes=10)
    queryset = Log.objects.filter(sn=log_storage.data.sn, \
                                  dateFin__gte=dateFinLower, \
                                  dateFin__lte=dateFinHigher)
    if queryset.count() == 0:
      logger.info("Log does NOT exist. Creating ...")
      log = Log()
      log.dateIni = log_storage.data.dateIni
      log.dateFin = log_storage.data.dateFin
      log.sn = log_storage.data.sn
      detector_queryset = Detector.objects.filter(id__in=log_storage.data.detectors)
      log.detectors = detector_queryset
      log.model = log_storage.data.model
      log.productId = log_storage.data.productId
      log.owner = log_storage.data.owner
      
      log.distanceTraveled = log_storage.data.distanceTraveled
      log.distanceToDetector = log_storage.data.distanceToDetector

      log.save()
    else:
      logger.info("Log does exist. Updating ...")
      log = queryset.first()
      log.distanceTraveled = log_storage.data.distanceTraveled
      log.distanceToDetector = log_storage.data.distanceToDetector
      log.save()



  def treat_message(self, req: WSRequestMessage):
    """
    treating message
    """
    if req.type == WSRequestMessage.DETECTOR:
      logger.info("Treating detector message")
      return self.treat_message_detector(req)
    elif req.type == WSRequestMessage.USER:
      logger.info("Treating user message")
    elif req.type == WSRequestMessage.INHIBITOR:
      logger.info("Treating inhibitor message")
  
  def calculate_distance(self, location1, location2):
    location_tuple_1 = (location1.lat, location1.lon)
    location_tuple_2 = (location2.lat, location2.lon)
    return geodesic(location_tuple_1, location_tuple_2).km * 1000            

  def treat_message_detector(self, req: WSRequestMessage):
    response_list = []
    try:
      logger.info("+++++++++++++++++++++++++++")
      logger.info("INIT: MESSAGE PROCESSING ")
      logger.info("+++++++++++++++++++++++++++")
      # Decode binary message
      coder = DetectorCoder()
      req.content = coder.decode(req.encoded)    

      # Print log
      logger.info("Received message detector={} from drone[sn]={} ".format(req.source_id, req.content.sn))

      # Get detector object
      detector = Detector.objects.get(id=req.source_id)
      logger.info("Identified detector as {}".format(detector.name))

      # Log Storage
      log_storage = None
      content = req.content
      if content.sn in self.__log_message_dict:
        # Already existing drone
        logger.info("Drone has been identified '{}'".format(content.sn))
        log_storage = self.__log_message_dict[content.sn]
        if not str(detector.id) in log_storage.data.detectors:
          log_storage.data.detectors.append(str(detector.id))
        # Update lastUpdate
        log_storage.update()

        log_storage.lastDetector = detector
        
        if content.driverLocation is not None:
          log_storage.data.driverLocation = content.driverLocation
        if content.homeLocation is not None:
          log_storage.data.homeLocation = content.homeLocation
        if content.droneLocation is not None:
          log_storage.data.maxHeight = max(log_storage.data.maxHeight, content.droneLocation.fHeight)
          if len(log_storage.data.route) > 0:
            lastLocation = log_storage.data.route[-1]
            distance = self.calculate_distance(content.droneLocation, lastLocation)            
            log_storage.data.distanceTraveled = log_storage.data.distanceTraveled + distance

          # distanceToDetector                    
          log_storage.data.distanceToDetector = \
            self.calculate_distance(content.droneLocation, detector.location)

          # Append item to route
          log_storage.data.route.append( copy.deepcopy(content.droneLocation) )
      else:
        # New Drone detected
        logger.info("Drone has been detected '{}'".format(content.sn))
        # Generate LogStorageMessage
        # NOTE: This model of data is veeery dark
        log_storage = LogStorageMessage()
        log_storage.detectors = [detector.id]
        log_storage.lastDetector = detector
        if content.sn is not None:
          log_storage.data.sn = content.sn
        if content.driverLocation is not None:
          log_storage.data.driverLocation = content.driverLocation
        if content.homeLocation is not None:
          log_storage.data.homeLocation = req.content.homeLocation
        if content.droneLocation is not None:
          log_storage.data.maxHeight = req.content.droneLocation.fHeight
          log_storage.data.droneLocation = req.content.droneLocation
          # Getting distance
          log_storage.data.distanceToDetector = \
            self.calculate_distance(req.content.droneLocation, detector.location)
        if content.productId is not None:
          log_storage.data.productId = req.content.productId
          try:
            drone_model = DroneModel.objects.get(productId=req.content.productId)
            log_storage.data.model = drone_model.name
          except Exception as e:
            print(str(e))
            logger.error("DroneModel with productId '{}' not found".format(req.content.productId))

          # Compute sendInfo
          try:
            drone = Drone.objects.get(sn=req.content.sn)
            log_storage.data.owner = drone.owner
            log_storage.sendInfo = not drone.hide
          except Exception as e:
            print(str(e))
            logger.info("Drone with sn '{}' not found. Sending info to user anyway".format(req.content.sn))
            # NOTE: sendInfo should be named 'processLog'
            log_storage.sendInfo = True

        # Increment msgCount
        log_storage.msgCount = log_storage.msgCount + 1

        # Add log_storage to dict
        self.__log_message_dict[req.content.sn] = log_storage

        
      # Send info if requested
      # print(req.content.__dict__)
      # print(log_storage.__dict__)
      if log_storage is not None and log_storage.sendInfo:

        # Store log locally
        self.save_log(log_storage)

        # NOTE: Sending info to users
        logger.info("Sending info to users ...")
        response_list = self.generate_response_list(detector, log_storage, req.content)
      
      logger.info("+++++++++++++++++++++++++++")
      logger.info("END: MESSAGE PROCESSING ")
      logger.info("+++++++++++++++++++++++++++")
    except Exception as e:
      print(str(e))
      logger.error("Error occurred while treating detector message")
    finally:
      return response_list

  def generate_response_list(self, detector, log_storage, data):
    response_list = []
    # groups related to detector
    groups_related_list = Group.objects.filter(devices__detectors__in=[detector.id])

    # Users related to detectors
    user_related_list = User.objects.filter(group__in=groups_related_list)
    user_related_list = [ str(user.id) for user in user_related_list ]

    # Potential 
    for user_id in user_related_list:
      message = {
        'deviceType' : 'detector',
        'messageType' : 'drone log',
        'deviceId' : str(detector.id),
        'deviceName' : str(detector.name),
        'data' : data,
      }
      message['data'] = {}
      message['data']['model'] = log_storage.data.model
      message['data']['owner'] = log_storage.data.owner
      message['data']['distanceTraveled'] = log_storage.data.distanceTraveled
      message['data']['msgCount'] = log_storage.msgCount
      response = WSResponseMessage(destination_id=user_id, type=WSResponseMessage.USER, content=json.dumps(message))
      response_list.append( response )

    return response_list


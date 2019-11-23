# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Python imports
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
      
  def treat_message_detector(self, req: WSRequestMessage):
    response_list = []
    try:
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
      if req.content.sn in self.__log_message_dict:
        # Already existing drone
        logger.info("Drone has been identified '{}'".format(req.content.sn))
        log_storage = self.__log_message_dict[req.content.sn]
        if not str(detector.id) in log_storage.data.detectors:
          log_storage.data.detectors.append(str(detector.id))
        # Update lastUpdate
        log_storage.update()

        log_storage.lastDetector = detector
        
        if req.content.driverLocation is not None:
          log_storage.data.driverLocation = req.content.driverLocation
        if req.content.homeLocation is not None:
          log_storage.data.homeLocation = req.content.homeLocation

        if req.content.droneLocation is not None:
          lastLocation = log_storage.data.route[-1] if len(log_storage.data.route) > 0 else None          
          detector_location = (detector.location.lat, detector.location.lon)

          if lastLocation is None:
            logger.info("Last location NOT found")
            log_storage.data.maxHeight = req.content.droneLocation.fHeight
            log_storage.data.distanceTraveled = 0            
          else:
            logger.info("Last location found")
            drone_last_location = (lastLocation.lat, lastLocation.lon)
            current_distanceTraveled = geodesic(detector_location, drone_last_location).km * 1000            
            log_storage.data.distanceTraveled = log_storage.data.distanceTraveled + current_distanceTraveled

          # distanceToDetector                    
          drone_location = (req.content.droneLocation.lat, req.content.droneLocation.lon)
          current_distanceToDetector = geodesic(drone_location, detector_location).km * 1000
          log_storage.data.distanceToDetector = current_distanceToDetector

          # Append item to route
          log_storage.data.route.append( req.content.droneLocation )
      else:
        # New Drone detected
        logger.info("Drone has been detected '{}'".format(req.content.sn))
        # Generate LogStorageMessage
        # NOTE: This model of data is veeery dark
        log_storage = LogStorageMessage()
        log_storage.detectors = [detector.id]
        log_storage.lastDetector = detector
        if req.content.sn is not None:
          log_storage.data.sn = req.content.sn
        if req.content.driverLocation is not None:
          log_storage.data.driverLocation = req.content.driverLocation
        if req.content.homeLocation is not None:
          log_storage.data.homeLocation = req.content.homeLocation
        if req.content.droneLocation is not None:
          log_storage.data.maxHeight = req.content.droneLocation.fHeight
          log_storage.data.droneLocation = req.content.droneLocation
          # Getting distance
          drone_location = (req.content.droneLocation.lat, req.content.droneLocation.lon)
          detector_location = (detector.location.lat, detector.location.lon)
          log_storage.data.distanceToDetector = geodesic(drone_location, detector_location).km * 1000
        if req.content.productId is not None:
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

        

        # NOTE: Call logsUpdate (within if)


      # Send info if requested
      # print(req.content.__dict__)
      # print(log_storage.__dict__)
      if log_storage is not None and log_storage.sendInfo:

        # Store log locally
        self.save_log(log_storage)

        # NOTE: Sending info to users
        logger.info("Sending info to users ...")
        response_list = self.generate_response_list(detector, log_storage, req.content)
        
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


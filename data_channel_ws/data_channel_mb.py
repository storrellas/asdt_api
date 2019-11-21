# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Python imports
import signal
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

# Create logger
logger = get_logger()
logger.propagate = False

class LogStorageDataMessage(LogMessage):
  dateIni = datetime.datetime.now()
  detectors = []
  sn = None
  model = None
  ownder = None
  route = []
  maxHeight = None
  distaceTraveled = None
  distanceToDetector = None
  model = None

class LogStorageMessage:
  lastUpdate = datetime.datetime.now()
  detectors = []
  detector = None
  sendInfo = False
  msgCount = 0
  data = LogStorageDataMessage()

  def __init__(self, detector):
    self.detectors = [detector.id]
    self.detector = detector

class WSRequestMessage:
  type = None
  source_id = None
  encoded = None
  content = None

  USER = 'USER'
  DETECTOR = 'DETECTOR'
  INHIBITOR = 'INHIBITOR'

  def __init__(self, type:str = None, source_id: str = None, encoded: bytearray = None, content: str = None):
    self.type = type
    self.source_id = source_id
    self.encoded = encoded
    self.content = content
    

class WSMessageBroker:
  
  # repository = LogMessageRepository()
  __log_dict = {}

  def treat_message(self, req: WSRequestMessage):
    """
    treating message
    """
    if req.type == WSRequestMessage.DETECTOR:
      logger.info("Treating detector message")
      self.treat_message_detector(req)
    elif req.type == WSRequestMessage.USER:
      logger.info("Treating user message")
    elif req.type == WSRequestMessage.INHIBITOR:
      logger.info("Treating inhibitor message")
      
  def treat_message_detector(self, req: WSRequestMessage):
    try:
      # Decode binary message
      coder = DetectorCoder()
      req.content = coder.decode(req.encoded)    

      # Print log
      logger.info("Received messgae {} from {} ".format(req.source_id, req.content))

      # Get detector object
      detector = Detector.objects.get(id=req.source_id)
      logger.info("Identified detector as {}".format(detector.name))

      # Log Storage
      if req.content.sn in self.__log_dict:
        logger.info("Drone has been detected '{}'".format(req.content.sn))
      else:
        logger.info("New Drone has been detected '{}'".format(req.content.sn))

        # NOTE: This model of data is veeery dark
        log_storage = LogStorageMessage(detector)
        if req.content.driverLocation is not None:
          log_storage.data.driverLocation = req.content.driverLocation
        if req.content.homeLocation is not None:
          log_storage.data.homeLocation = req.content.homeLocation
        if req.content.droneLocation is not None:
          log_storage.data.maxHeight = req.content.droneLocation.fHeight
          log_storage.data.droneLocation = req.content.droneLocation
          # Getting distance
          drone_location = (info.droneLocation.lat, info.droneLocation.lon)
          detector_location = (detector.location.lat, detector.location.lon)
          log_storage.distanceToDetector = geodesic(drone_location, detector_location)

        if req.content.productId is not None:
          log_storage.data.productId = req.content.productId

        self.__log_dict[req.content.sn] = log

        # NOTE: Call logsUpdate



    except Exception as e:
      print(str(e))
      logger.error("Error occurred while treating detector message")


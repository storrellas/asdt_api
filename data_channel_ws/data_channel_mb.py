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

# Mongoengine connect
import mongoengine

# Project imports
from common.utils import get_logger
from common import DetectorCoder

from models import ConnectionLog
from user.models import User
from detectors.models import Detector
from inhibitors.models import Inhibitor
from groups.models import Group

# Create logger
logger = get_logger()
logger.propagate = False

class LogRepository:
  """
  Repository of the Logs
  """

  __log_list = []

  def add(self, item):
    """
    Adds a client
    """
    self.__log_list.append(item)

  def remove(self, item):
    """
    Remove a client
    """
    self.__log_list.remove(item)


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
  
  repository = None

  def __init__(self, repository=[]):
    self.repository = repository

  def treat_message(self, req: WSRequestMessage):
    """
    treating message
    """
    print("req.type", req.type)
    if req.type == WSRequestMessage.DETECTOR:
      logger.info("Treating detector message")
      self.treat_message_detector(req)
    elif req.type == WSRequestMessage.USER:
      logger.info("Treating user message")
    elif req.type == WSRequestMessage.INHIBITOR:
      logger.info("Treating inhibitor message")
      
  def treat_message_detector(self, req: WSRequestMessage):
    try:

      coder = DetectorCoder()
      req.content = coder.decode(req.encoded)    
      print(req.content.__dict__)

      logger.info("Received messgae {} from {} ".format(req.source_id, req.content))

      detector = Detector.objects.get(id=req.source_id)
      logger.info("Identified detector as {}".format(detector.name))
    except Exception as e:
      print(str(e))
      logger.error("Detector not found")


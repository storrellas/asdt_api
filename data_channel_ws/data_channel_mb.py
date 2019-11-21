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


class WSRequestMessage:
  type = None
  source_id = None
  encoded = None
  content = None

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
    logger.info("Received messgae {} from {} ".format(req.source_id, req.content))

    if req.type == 'detector':
      logger.info("Treating detector message")
      self.treat_message_detector(input_message)
    elif req.type == 'user':
      logger.info("Treating user message")
    elif req.type == 'inhibitor':
      logger.info("Treating inhibitor message")
      
  def treat_message_detector(self, req: WSRequestMessage):
    try:
      detector = Detector.objects.get(id=req.source_id)
      logger.info("Identified detector as {}".format(detector.name))
    except Exception as e:
      print(str(e))
      logger.error("Detector not found")


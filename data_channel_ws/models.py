# Mongoengine imports
from mongoengine import *
import datetime

from asdt_api.models import ASDTDocument
from user.models import User
from detectors.models import Detector
from inhibitors.models import Inhibitor

class ConnectionLog(ASDTDocument):
  meta = {'collection': 'connectionlogs'}

  user = ReferenceField(User, reverse_delete_rule = NULLIFY)
  detector = ReferenceField(Detector, reverse_delete_rule = NULLIFY)
  inhibitor = ReferenceField(Inhibitor, reverse_delete_rule = NULLIFY)

  userName = StringField(required=True, default='')
  detectorName = StringField(required=True, default='')
  inhibitorName = StringField(required=True, default='')

  USER = 'USER'
  DETECTOR = 'DETECTOR'
  INHIBITOR = 'INHIBITOR'
  type_list = [USER, DETECTOR, INHIBITOR]
  type = StringField(choices=type_list, default=USER)

  CONNECTION = 'CONNECTION'
  DISCONNECTION = 'DISCONNECTION'
  reason_list = [CONNECTION, DISCONNECTION]

  reason = StringField(choices=reason_list, default=CONNECTION)
import os, sys, bcrypt
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asdt_api.settings")

# Django import
from django.conf import settings

# Project imports
from user.models import *
from logs.models import *
from bson.objectid import ObjectId
from asdt_api import utils

# Import mongoengine
import mongoengine

logger = utils.get_logger()

# Connect mongo
mongoengine.connect(settings.MONGO_DB, host=settings.MONGO_HOST, port=int(settings.MONGO_PORT))
logger.info("Connected MONGODB against mongodb://{}:{}/{}".format(settings.MONGO_HOST, settings.MONGO_PORT, settings.MONGO_DB))


# Delete entities
logger.info("Deleting entities ...")
User.objects.all().delete()
Group.objects.all().delete()
Detector.objects.all().delete()
Inhibitor.objects.all().delete()
Log.objects.all().delete()
logger.info("Done!")

# Groups
##############
logger.info("Creating groups ...")
root_group = Group.objects.create(name='ASDT')
logger.info("Created {}. Done!".format(Group.objects.all().count()) )

# Users
##############
logger.info("Creating users ...")
master = User.objects.create(email='master@asdt.com', name='master', role='MASTER')
master.set_password('asdt2019')

# Create admin
circle_zone = CircleZone(center=CircleZoneCenter(longitude=1.2, latitude=2.3),
                         radius=1.0, color="blue", opacity="1.0", 
                         id="123", droneID=["456"], visible=True, active=False)
display_options = DisplayOptions(mapType='MyMap', zone=[[2,3]],circleZone=[circle_zone])
admin = User.objects.create(email='admin@asdt.com', name='admin', 
                            password='asdt2019', role='ADMIN',
                            displayOptions=display_options)
admin.set_password('asdt2019')
root_group.users.append(admin)
root_group.save()

empowered = User.objects.create(email='empowered@asdt.com', name='empowered', password='asdt2019', role='EMPOWERED')
empowered.set_password('asdt2019')
viewer = User.objects.create(email='viewer@asdt.com', name='viewer', password='asdt2019', role='VIEWER')
viewer.set_password('asdt2019')
logger.info("Created {}. Done!".format(User.objects.all().count()) )


# Detectors
##############
logger.info("Creating detectors ...")
detector = Detector.objects.create(name='moncloa', password='asdt2019', 
                        location=DetectorLocation(lat=0, lon=0, height=0))
root_group.devices.detectors.append(detector)
root_group.save()
Detector.objects.create(name='zarzuela', password='asdt2019', 
                        location=DetectorLocation(lat=0, lon=0, height=0))
Detector.objects.create(name='congreso', password='asdt2019', 
                        location=DetectorLocation(lat=0, lon=0, height=0))
Detector.objects.create(name='cuatrovientos', password='asdt2019', 
                        location=DetectorLocation(lat=0, lon=0, height=0))
Detector.objects.create(name='canillas', password='asdt2019', 
                        location=DetectorLocation(lat=0, lon=0, height=0))
logger.info("Created {}. Done!".format(Detector.objects.all().count()) )


# class LogCenterPoint(EmbeddedDocument):
#   lat = FloatField(default=0.0)
#   lon = FloatField(default=0.0)
#   aHeight = FloatField(default=0.0)
#   fHeight = FloatField(default=0.0)

# class LogRoute(EmbeddedDocument):
#   _id = ObjectIdField()
#   time = DateTimeField(default=datetime.datetime.now)
#   lat = FloatField(default=0.0)
#   lon = FloatField(default=0.0)
#   aHeight = FloatField(default=0.0)
#   fHeight = FloatField(default=0.0)

# class LogBoundingBox(EmbeddedDocument):
#   maxLat = FloatField(default=0.0)
#   maxLon = FloatField(default=0.0)
#   minLat = FloatField(default=0.0)
#   minLon = FloatField(default=0.0)


# class Log(ASDTDocument):
#   meta = {'collection': 'logs'}

#   # timestamps
#   dateIni = DateTimeField(default=datetime.datetime.now)
#   dateFin = DateTimeField(default=datetime.datetime.now)
#   sn = StringField(default='')

#   detectors = ListField(ReferenceField(Detector, reverse_delete_rule = NULLIFY))

#   model = StringField(default='')
#   productId = IntField(default=-1)
#   owner = StringField(default='')

#   driverLocation = EmbeddedDocumentField(Location)
#   homeLocation = EmbeddedDocumentField(Location)
#   maxHeight = FloatField(default=0.0)
#   distanceTravelled = FloatField(default=0.0)
#   distanceToDetector = FloatField(default=0.0)
#   centerPoint = EmbeddedDocumentField(LogCenterPoint, default=LogCenterPoint())
#   boundingBox = EmbeddedDocumentField(LogBoundingBox, default=LogCenterPoint())
#   route = EmbeddedDocumentListField(LogRoute, default=[])

# Detectors
##############
logger.info("Creating logs ...")
route = [
  LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
  LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
  LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
  LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
  LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
  LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
  LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3)
]
Log.objects.create(dateIni=datetime.datetime.strptime('2019-09-01T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                    dateFin=datetime.datetime.strptime('2019-09-01T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                    model='ABC', sn='123', productId=1234,
                    driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                    maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                    centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                    boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3))
Log.objects.create(dateIni=datetime.datetime.strptime('2019-10-21T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                    dateFin=datetime.datetime.strptime('2019-10-21T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                  model='ABC', sn='123', productId=1234,
                  driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                  maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                  centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                  boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3))
Log.objects.create(dateIni=datetime.datetime.strptime('2019-10-22T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                    dateFin=datetime.datetime.strptime('2019-10-22T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                  model='ABC', sn='123', productId=1234,
                  driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                  maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                  centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                  boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3))                                    
logger.info("Created {}. Done!".format(Log.objects.all().count()) )


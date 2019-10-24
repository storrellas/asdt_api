import os

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


# class CircleZoneCenter(EmbeddedDocument):
#   longitude = FloatField(default=0.0)
#   latitude = FloatField(default=0.0)

# class CircleZone(EmbeddedDocument):
#   _id = ObjectIdField()
#   center = EmbeddedDocumentField(CircleZoneCenter, default=CircleZoneCenter())
#   radius = IntField(default=0)
#   color = StringField(default='')
#   opacity = StringField(default='')
#   id = StringField(default='')
#   droneID = ListField(StringField())
#   visible = BooleanField(default=False)
#   active = BooleanField(default=False)

# class DisplayOptions(EmbeddedDocument):
#   mapType = StringField(default='')
#   zone = ListField(ListField(IntField()))
#   circleZone = EmbeddedDocumentListField(CircleZone, default=[])


# Users
##############
logger.info("Creating users ...")
master = User.objects.create(email='master@asdt.com', name='master', password='asdt2019', role='MASTER')

# Create admin
circle_zone = CircleZone(center=CircleZoneCenter(longitude=1.2, latitude=2.3),
                         radius=1.0, color="blue", opacity="1.0", 
                         id="123", droneID=["456"], visible=True, active=False)
display_options = DisplayOptions(mapType='MyMap', zone=[[2,3]],circleZone=[circle_zone])
admin = User.objects.create(email='admin@asdt.com', name='admin', 
                            password='asdt2019', role='ADMIN',
                            displayOptions=display_options)
root_group.users.append(admin)
root_group.save()

empowered = User.objects.create(email='empowered@asdt.com', name='empowered', password='asdt2019', role='EMPOWERED')
viewer = User.objects.create(email='viewer@asdt.com', name='viewer', password='asdt2019', role='VIEWER')
logger.info("Created {}. Done!".format(User.objects.all().count()) )


# Detectors
##############
logger.info("Creating detectors ...")
Detector.objects.create(name='moncloa', password='asdt2019', 
                        location=DetectorLocation(lat=0, lon=0, height=0))
Detector.objects.create(name='zarzuela', password='asdt2019', 
                        location=DetectorLocation(lat=0, lon=0, height=0))
Detector.objects.create(name='congreso', password='asdt2019', 
                        location=DetectorLocation(lat=0, lon=0, height=0))
Detector.objects.create(name='cuatrovientos', password='asdt2019', 
                        location=DetectorLocation(lat=0, lon=0, height=0))
Detector.objects.create(name='canillas', password='asdt2019', 
                        location=DetectorLocation(lat=0, lon=0, height=0))
logger.info("Created {}. Done!".format(Detector.objects.all().count()) )
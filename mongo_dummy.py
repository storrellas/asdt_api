import os, sys, bcrypt
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asdt_api.settings")

# Django import
from django.conf import settings

# Project imports
from user.models import *
from groups.models import *
from logs.models import *
from drones.models import *
from bson.objectid import ObjectId
from asdt_api import utils

# Import mongoengine
import mongoengine

logger = utils.get_logger()

class MongoDummy:

  def setup(self, db, host, port):
    # Connect mongo    
    mongoengine.connect(db, host=host, port=port)
    logger.info("Connected MONGODB against mongodb://{}:{}/{}".format(settings.MONGO_HOST, settings.MONGO_PORT, settings.MONGO_DB))

  def default_route(self):
    return [
      LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
      LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
      LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
      LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
      LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
      LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
      LogRoute(time=datetime.datetime.now(), lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3)
    ]

  def clean(self):
    # Delete entities
    logger.info("Deleting entities ...")
    User.objects.all().delete()
    Group.objects.all().delete()
    Detector.objects.all().delete()
    Inhibitor.objects.all().delete()
    Log.objects.all().delete()
    DroneModel.objects.all().delete()
    logger.info("Done!")

  def generate_scenario(self):
    self.clean()

    # Groups
    ##############
    logger.info("Creating groups ...")
    viewer_group = Group.objects.create(name='VIEWER_ASDT', 
                                        devices=GroupDevices()) 
    admin_child_child_group = Group.objects.create(name='ADMIN_CHILD_CHILD_ASDT', 
                                                    devices=GroupDevices())
    admin_child_child2_group = Group.objects.create(name='ADMIN_CHILD_CHILD2_ASDT', 
                                                    devices=GroupDevices())
    admin_child_group = Group.objects.create(name='ADMIN_CHILD_ASDT', 
                                            childs=[admin_child_child_group, admin_child_child2_group], 
                                            devices=GroupDevices())
    admin_child2_group = Group.objects.create(name='ADMIN_CHILD2_ASDT', 
                                            devices=GroupDevices())
    admin_group = Group.objects.create(name='ADMIN_ASDT', childs=[admin_child_group, admin_child2_group], 
                                            devices=GroupDevices())
    
    # Configura parents
    admin_child_child_group.parent = admin_child_group
    admin_child_child_group.save()
    admin_child_child2_group.parent = admin_child_group
    admin_child_child2_group.save()
    admin_child_group.parent = admin_group
    admin_child_group.save()
    admin_child2_group.parent = admin_group
    admin_child2_group.save()


    logger.info("Created {}. Done!".format(Group.objects.all().count()) )

    # Users
    ##############
    logger.info("Creating users ...")
    admin_a = User.objects.create(email='a@a.com', name='admin', role='ADMIN')
    admin_a.set_password('asdt2019')

    master = User.objects.create(email='master@asdt.eu', name='master', role='MASTER')
    master.set_password('asdt2019')

    # Create admin - group : admin_group
    circle_zone = CircleZone(center=CircleZoneCenter(longitude=1.2, latitude=2.3),
                            radius=1.0, color="blue", opacity="1.0", 
                            id="123", droneID=["456"], visible=True, active=False)
    display_options = DisplayOptions(mapType='MyMap', zone=[[2,3]],circleZone=[circle_zone])
    admin = User.objects.create(email='admin@asdt.eu', name='admin', 
                                password='asdt2019', role='ADMIN',
                                displayOptions=display_options,
                                group=admin_group, hasGroup=True)
    admin.set_password('asdt2019')

    # Create admin_child - group : admin_child_group
    admin_child = User.objects.create(email='admin_child@asdt.eu', name='admin', 
                                password='asdt2019', role='ADMIN',
                                displayOptions=display_options,
                                group=admin_child_group, hasGroup=True)
    admin_child.set_password('asdt2019')

    # Create admin_child_child - group : admin_child_child_group
    admin_child_child = User.objects.create(email='admin_child_child@asdt.eu', name='admin', 
                                password='asdt2019', role='ADMIN',
                                displayOptions=display_options,
                                group=admin_child_child_group, hasGroup=True)
    admin_child_child.set_password('asdt2019')

    empowered = User.objects.create(email='empowered@asdt.eu', name='empowered', password='asdt2019', role='EMPOWERED')
    empowered.set_password('asdt2019')
    viewer = User.objects.create(email='viewer@asdt.eu', name='viewer', password='asdt2019', role='VIEWER',
                                  group=viewer_group, hasGroup=True)
    viewer.set_password('asdt2019')
    logger.info("Created {}. Done!".format(User.objects.all().count()) )

    # Add to groups
    admin_group.users.append(admin)
    admin_group.save()
    admin_child_group.users.append(admin_child)
    admin_child_group.save()
    admin_child_child_group.users.append(admin_child_child)
    admin_child_child_group.save()
    viewer_group.users.append(viewer)
    viewer_group.save()


    # Detectors
    ##############
    logger.info("Creating detectors ...")
    detector1 = Detector.objects.create(name='moncloa', password='asdt2019', 
                            location=DetectorLocation(lat=0, lon=0, height=0))
    detector2 = Detector.objects.create(name='zarzuela', password='asdt2019', 
                            location=DetectorLocation(lat=0, lon=0, height=0))
    detector3 = Detector.objects.create(name='congreso', password='asdt2019', 
                            location=DetectorLocation(lat=0, lon=0, height=0))
    detector4 = Detector.objects.create(name='cuatrovientos', password='asdt2019', 
                            location=DetectorLocation(lat=0, lon=0, height=0))
    detector5 = Detector.objects.create(name='canillas', password='asdt2019', 
                            location=DetectorLocation(lat=0, lon=0, height=0))
    logger.info("Created {}. Done!".format(Detector.objects.all().count()) )

    # Add to groups
    admin_group.devices.detectors = [detector2]
    admin_group.save()
  
    viewer_group.devices.detectors = [detector3]
    viewer_group.save()

    admin_child_group.devices.detectors = [detector4]
    admin_child_group.save()

    admin_child_child_group.devices.detectors = [detector5]
    admin_child_child_group.save()


    # Logs
    ##############
    logger.info("Creating logs ...")
    route = self.default_route()
    Log.objects.create(dateIni=datetime.datetime.strptime('2019-09-01T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                        dateFin=datetime.datetime.strptime('2019-09-01T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                        model='ABC', sn='1', productId=1234,
                        detectors=[detector1, detector2],
                        driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                        maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                        centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                        boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3), route=route)
    Log.objects.create(dateIni=datetime.datetime.strptime('2019-10-21T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                        dateFin=datetime.datetime.strptime('2019-10-21T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                      model='ABC', sn='2', productId=1234,
                      detectors=[detector1, detector2],
                      driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                      maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                      centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                      boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3), route=route)  
    Log.objects.create(dateIni=datetime.datetime.strptime('2019-10-22T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                        dateFin=datetime.datetime.strptime('2019-10-22T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                      model='ABC', sn='3', productId=1234,
                      detectors=[detector1, detector3],
                      driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                      maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                      centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                      boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3), route=route)
    Log.objects.create(dateIni=datetime.datetime.strptime('2019-10-24T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                        dateFin=datetime.datetime.strptime('2019-10-24T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                      model='ABC', sn='4', productId=1234,
                      detectors=[detector1, detector4],
                      driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                      maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                      centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                      boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3), route=route)                  
    logger.info("Created {}. Done!".format(Log.objects.all().count()) )


    # Model
    ##############
    logger.info("Creating models ...")
    DroneModel.objects.create(name='Mavic', productId=16, imageType='image/png', 
                              imageUrl='/api/v2/media/drones/model/16.png', image=True, imageCode=1)
    DroneModel.objects.create(name='Phantom', productId=20, imageType='image/png', 
                              imageUrl='/api/v2/media/drones/model/20.png', image=True, imageCode=1)
    DroneModel.objects.create(name='Mavic Pro', productId=18, imageType='image/png', 
                              imageUrl='/api/v2/media/drones/model/18.png', image=True, imageCode=1)
    DroneModel.objects.create(name='DJI MAVIC PRO DUAL', productId=51, imageType='image/png', 
                              imageUrl='/api/v2/media/drones/model/51.png', image=True, imageCode=1)
    logger.info("Created {}. Done!".format(DroneModel.objects.all().count()) )


  def generate_scenario2(self):
    self.clean()

    # Groups
    ##############
    logger.info("Creating groups ...")
    viewer_group = Group.objects.create(name='VIEWER_ASDT', 
                                        devices=GroupDevices()) 
    admin_child_child_group = Group.objects.create(name='ADMIN_CHILD_CHILD_ASDT', 
                                                    devices=GroupDevices())
    admin_child_child2_group = Group.objects.create(name='ADMIN_CHILD_CHILD2_ASDT', 
                                                    devices=GroupDevices())
    admin_child_group = Group.objects.create(name='ADMIN_CHILD_ASDT', 
                                            childs=[admin_child_child_group, admin_child_child2_group], 
                                            devices=GroupDevices())
    admin_child2_group = Group.objects.create(name='ADMIN_CHILD2_ASDT', 
                                            devices=GroupDevices())
    admin_group = Group.objects.create(name='ADMIN_ASDT', childs=[admin_child_group, admin_child2_group], 
                                            devices=GroupDevices())




    # Configura parents
    admin_child_child_group.parent = admin_child_group
    admin_child_child_group.save()
    admin_child_child2_group.parent = admin_child_group
    admin_child_child2_group.save()
    admin_child_group.parent = admin_group
    admin_child_group.save()
    admin_child2_group.parent = admin_group
    admin_child2_group.save()


    logger.info("Created {}. Done!".format(Group.objects.all().count()) )





    # Users
    ##############
    logger.info("Creating users ...")
    admin_a = User.objects.create(email='a@a.com', name='admin', role='ADMIN')
    admin_a.set_password('asdt2019')

    master = User.objects.create(email='master@asdt.eu', name='master', role='MASTER')
    master.set_password('asdt2019')

    # Create admin - group : admin_group
    circle_zone = CircleZone(center=CircleZoneCenter(longitude=1.2, latitude=2.3),
                            radius=1.0, color="blue", opacity="1.0", 
                            id="123", droneID=["456"], visible=True, active=False)
    display_options = DisplayOptions(mapType='MyMap', zone=[[2,3]],circleZone=[circle_zone])
    admin = User.objects.create(email='admin@asdt.eu', name='admin', 
                                password='asdt2019', role='ADMIN',
                                displayOptions=display_options,
                                group=admin_group, hasGroup=True)
    admin.set_password('asdt2019')

    # Create admin_child - group : admin_child_group
    admin_child = User.objects.create(email='admin_child@asdt.eu', name='admin', 
                                password='asdt2019', role='ADMIN',
                                displayOptions=display_options,
                                group=admin_child_group, hasGroup=True)
    admin_child.set_password('asdt2019')

    # Create admin_child_child - group : admin_child_child_group
    admin_child_child = User.objects.create(email='admin_child_child@asdt.eu', name='admin', 
                                password='asdt2019', role='ADMIN',
                                displayOptions=display_options,
                                group=admin_child_child_group, hasGroup=True)
    admin_child_child.set_password('asdt2019')

    empowered = User.objects.create(email='empowered@asdt.eu', name='empowered', password='asdt2019', role='EMPOWERED')
    empowered.set_password('asdt2019')
    viewer = User.objects.create(email='viewer@asdt.eu', name='viewer', password='asdt2019', role='VIEWER',
                                  group=viewer_group, hasGroup=True)
    viewer.set_password('asdt2019')
    logger.info("Created {}. Done!".format(User.objects.all().count()) )

    # Add to groups
    admin_group.users.append(admin)
    admin_group.save()
    admin_child_group.users.append(admin_child)
    admin_child_group.save()
    admin_child_child_group.users.append(admin_child_child)
    admin_child_child_group.save()
    viewer_group.users.append(viewer)
    viewer_group.save()


    # Detectors
    ##############
    logger.info("Creating detectors ...")
    detector1 = Detector.objects.create(name='moncloa', password='asdt2019', 
                            location=DetectorLocation(lat=0, lon=0, height=0))
    detector2 = Detector.objects.create(name='zarzuela', password='asdt2019', 
                            location=DetectorLocation(lat=0, lon=0, height=0))
    detector3 = Detector.objects.create(name='congreso', password='asdt2019', 
                            location=DetectorLocation(lat=0, lon=0, height=0))
    detector4 = Detector.objects.create(name='cuatrovientos', password='asdt2019', 
                            location=DetectorLocation(lat=0, lon=0, height=0))
    detector5 = Detector.objects.create(name='canillas', password='asdt2019', 
                            location=DetectorLocation(lat=0, lon=0, height=0))
    logger.info("Created {}. Done!".format(Detector.objects.all().count()) )

    # Add to groups
    admin_group.devices.detectors = [detector2]
    admin_group.save()
  
    viewer_group.devices.detectors = [detector3]
    viewer_group.save()

    admin_child_group.devices.detectors = [detector4]
    admin_child_group.save()

    admin_child_child_group.devices.detectors = [detector5]
    admin_child_child_group.save()


    # Logs
    ##############
    logger.info("Creating logs ...")
    route = self.default_route()
    Log.objects.create(dateIni=datetime.datetime.strptime('2019-09-01T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                        dateFin=datetime.datetime.strptime('2019-09-01T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                        model='ABC', sn='1', productId=1234,
                        detectors=[detector1, detector2],
                        driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                        maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                        centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                        boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3), route=route)
    Log.objects.create(dateIni=datetime.datetime.strptime('2019-10-21T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                        dateFin=datetime.datetime.strptime('2019-10-21T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                      model='ABC', sn='2', productId=1234,
                      detectors=[detector1, detector2],
                      driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                      maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                      centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                      boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3), route=route)  
    Log.objects.create(dateIni=datetime.datetime.strptime('2019-10-22T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                        dateFin=datetime.datetime.strptime('2019-10-22T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                      model='ABC', sn='3', productId=1234,
                      detectors=[detector1, detector3],
                      driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                      maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                      centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                      boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3), route=route)
    Log.objects.create(dateIni=datetime.datetime.strptime('2019-10-24T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"), 
                        dateFin=datetime.datetime.strptime('2019-10-24T23:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ"),
                      model='ABC', sn='4', productId=1234,
                      detectors=[detector1, detector4],
                      driverLocation=Location(lat=1.2,lon=3.4), homeLocation=Location(lat=1.2,lon=3.4),
                      maxHeight=12, distanceTravelled=12, distanceToDetector=12,
                      centerPoint=LogCenterPoint(lat=1.0, lon=2.0, aHeight=1.2, fHeight=2.3),
                      boundingBox=LogBoundingBox(maxLat=1.0, maxLon=2.0, minLat=1.2, minLon=2.3), route=route)                  
    logger.info("Created {}. Done!".format(Log.objects.all().count()) )


    # Model
    ##############
    logger.info("Creating models ...")
    DroneModel.objects.create(name='Mavic', productId=16, imageType='image/png', 
                              imageUrl='/api/v2/media/drones/model/16.png', image=True, imageCode=1)
    DroneModel.objects.create(name='Phantom', productId=20, imageType='image/png', 
                              imageUrl='/api/v2/media/drones/model/20.png', image=True, imageCode=1)
    DroneModel.objects.create(name='Mavic Pro', productId=18, imageType='image/png', 
                              imageUrl='/api/v2/media/drones/model/18.png', image=True, imageCode=1)
    DroneModel.objects.create(name='DJI MAVIC PRO DUAL', productId=51, imageType='image/png', 
                              imageUrl='/api/v2/media/drones/model/51.png', image=True, imageCode=1)
    logger.info("Created {}. Done!".format(DroneModel.objects.all().count()) )

if __name__ == "__main__":
  mongo_dummy = MongoDummy()
  mongo_dummy.setup(settings.MONGO_DB, settings.MONGO_HOST, int(settings.MONGO_PORT))
  mongo_dummy.generate_scenario()



  # user = User.objects.get(email='admin@asdt.eu')
  # user.group


  # queryset = Log.objects.all()
  # # Allowed detector list
  # detector_list_for_user = []
  # for detector in user.group.devices.detectors:
  #     detector_list_for_user.append( detector.fetch() )

  # print(len(detector_list_for_user) )
  # for detector in detector_list_for_user:
  #   print(detector)
  #   print(detector.to_mongo().to_dict())

  # #queryset = queryset.filter(detectors__in=[detector_list_for_user])
  # for item in queryset:
  #   print(item.detectors[0])
  #   print(item.detectors[0].to_json())
  #   print(item.detectors[0].as_pymongo())
  #   print(item.detectors[0].to_mongo())

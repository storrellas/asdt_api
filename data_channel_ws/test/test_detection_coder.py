# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Python imports
import unittest

# Testing files
from common import DetectorCoder, LogMessage, LogLocationMessage


class TestCase(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    """
    Called once in every suite
    """
    super().setUpClass()
    # logger.info("----------------------------")
    # logger.info("--- Generating scenario  ---")
    # logger.info("----------------------------")    
    # settings.MONGO_DB = 'asdt_test'
    # logger.info("DB Generated: {}".format(settings.MONGO_DB))

    # mongo_dummy = MongoDummy()
    # mongo_dummy.setup(settings.MONGO_DB, settings.MONGO_HOST, int(settings.MONGO_PORT))
    # mongo_dummy.generate_scenario()

  def check_range(self, target, candidate):
    return target - 1 < candidate < target + 1

  def check_location(self, target, candidate):
    cond1 = self.check_range(target.lat, candidate.lat)
    cond2 = self.check_range(target.lon, candidate.lon)
    return cond1 and cond2


  def test_coder_decoder(self):
    coder = DetectorCoder()

    # Dummy LogMessage
    driverLocation = LogLocationMessage(lat=41.2, lon=2.3)
    droneLocation = LogLocationMessage(lat=41.2, lon=2.3, fHeight=8.8)
    homeLocation = LogLocationMessage(lat=41.2, lon=2.3)
    log = LogMessage(sn='111BBBBBBBBB16', driverLocation=driverLocation,
                      droneLocation=droneLocation, homeLocation=homeLocation,
                      productId=16)

    # Encode frame
    encoded = coder.encode( log ) 
    decoded = coder.decode( encoded )

    # Check type is correct
    self.assertTrue( isinstance(encoded, bytearray) )

    # Check fields
    self.assertEqual( log.sn, decoded.sn )
    self.assertEqual( log.productId, decoded.productId )  
    self.assertTrue( self.check_location(log.driverLocation, decoded.driverLocation) )
    self.assertTrue( self.check_location(log.droneLocation, decoded.droneLocation) )
    self.assertTrue( self.check_range(log.droneLocation.fHeight, decoded.droneLocation.fHeight) )
    self.assertTrue( self.check_location(log.homeLocation, decoded.homeLocation) )

    # print("----- ENCODING ---")
    # print("log", log)
    # print("encoded", encoded)

    # print("----- DECODING ---")
    # print("decoded", decoded.__dict__)



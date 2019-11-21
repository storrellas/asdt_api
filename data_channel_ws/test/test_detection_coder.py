# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Testing files
from common import DetectorCoder, LogMessage, LogLocationMessage


if __name__ == "__main__":

  print("----- ENCODING ---")

  coder = DetectorCoder()



  # LogMessage
  driverLocation = LogLocationMessage(lat=41.2, lon=2.3)
  droneLocation = LogLocationMessage(lat=41.2, lon=2.3, fHeight=8.8, aHeight=1)
  homeLocation = LogLocationMessage(lat=41.2, lon=2.3)
  log = LogMessage(sn='111BBBBBBBBB16', driverLocation=driverLocation,
                    droneLocation=droneLocation, homeLocation=homeLocation,
                    productId=16)

  # Encode frame
  encoded = coder.encode( log ) 
  print("log", log)
  print("encoded", encoded)

  print("----- DECODING ---")
  decoded = coder.decode( encoded )
  print("decoded", decoded.__dict__)


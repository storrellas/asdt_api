# Update syspath
import os, sys
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Testing files
from common import DetectorCoder


if __name__ == "__main__":

  print("----- ENCODING ---")

  coder = DetectorCoder()

  # Generate package
  info = coder.template()
  info['sn'] = '111BBBBBBBBB16'

  info['driverLocation']['lat'] = 41.2
  info['driverLocation']['lon'] = 2.3  

  info['droneLocation']['lat'] = 41.2
  info['droneLocation']['lon'] = 2.3
  info['droneLocation']['fHeight'] = 8.8
  info['droneLocation']['aHeight'] = 1

  info['homeLocation']['lat'] = 41.2
  info['homeLocation']['lon'] = 2.3

  info['driverLocation']['lat'] = 41.2
  info['driverLocation']['lon'] = 2.3

  info['productId'] = 16



  # Encode frame
  encoded = coder.encode( info ) 
  print("info", info)
  print("encoded", encoded)

  print("----- DECODING ---")
  decoded = coder.decode( encoded )
  print("decoded", decoded)

  print(decoded == info)
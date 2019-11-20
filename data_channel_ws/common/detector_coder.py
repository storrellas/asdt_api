from .utils import get_logger

logger = get_logger()


class DetectorCoder:

  __toDegrees = 174533.0

  def template(self):
    """
    Holds the basic template info
    NOTE: We should migrate this to a POJO
    """
    info = { 
      'sn': '', 
      'driverLocation': { 
        'lat': 0, 'lon': 0,
        #'fHeight': 0, 'aHeight': 0 
      },
      'droneLocation': { 
        'lat': 0, 'lon': 0,
        'fHeight': 0, 'aHeight': 0 
      }, 
      'vx': 0,
      'vy': 0,
      'vz': 0,
      'pitch': 0,
      'roll': 0,
      'yaw': 0,
      'homeLocation': { 'lat': 0, 'lon': 0 }, 
      'driverLocation': { 'lat': 0, 'lon': 0 }, 
      'productId': 0,
      'uuid': ''
    }

    return info

  def _encode109(self, info):

    # Declare frame
    frame = bytearray(109)
    frame[11] = 0x1F

    # 25 -> + 14 bytes [serial number] (string)
    sn_ba = bytearray(info['sn'], 'utf-8')
    #sn_ba = bytearray()
    #sn_ba.extend(map(ord, info['sn']))
    frame[25:25+len(sn_ba)] = sn_ba
   
    # 41 -> + 4 bytes [long drone]    
    lon = int(info['droneLocation']['lon'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[41:41+4] = lon
    # 45 -> + 4 byes [lat drone]
    lat = int(info['droneLocation']['lat'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[45:45+4] = lat

    # 49 -> + 2 bytes [absolute height] - NOTE: aHeight does not exist
    # aHeight = int(info['droneLocation']['aHeight'] * self.__toDegrees).to_bytes(2, 'little', signed=True)
    # frame[49:49+2] = aHeight
    # 51 -> + 2 bytes [floor height]
    # fHeight = int(info['droneLocation']['fHeight'] * 10).to_bytes(2, 'little', signed=True)
    # frame[51:51+2] = fHeight

    # NOTE: WATCH OUT THIS ONE IS LAT first, LON second
    # 69 -> + 4 bytes [lat driver] 
    lat = int(info['driverLocation']['lat'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[69:69+4] = lat
    # 73 -> + 4 bytes [lon driver]
    lon = int(info['driverLocation']['lon'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[73:73+4] = lon

    # 77 -> + 4 bytes [lon home]
    lon = int(info['homeLocation']['lon'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[77:77+4] = lon
    # 81 -> + 4 bytes [lat home]
    lat = int(info['homeLocation']['lat'] * self.__toDegrees).to_bytes(4, 'little', signed=True)
    frame[81:81+4] = lat

    # 85 -> + 1 byte [product type]
    productId = int(info['productId']).to_bytes(1, 'little', signed=False)
    frame[85:85] = productId

    #print(frame)
    return frame

  def encode(self, info):
    return self._encode109(info)

  def decode(self, data):
    # Check length is ok
    if len(data) < 11:
      return None

    # Check data_type
    data_type = data[11]
    if data_type == 0x1F:
      return self.decode1(data)
    elif data_type == 0x7F:
      logger.info("decode2")
      return "decode2"
    elif data_type == 0xE5:
      logger.info("decode2")
      return "decode3"
    elif data_type == 0x9E:
      logger.info("decode4")
      return "decode4"

    return None

  def decode1(self, data):
    """
    Decodes message comming from detector
    """
    # Check length of sn
    snLength = 0
    snOffset = 25
    while data[snOffset+snLength] != 0x00:
      snLength = snLength + 1

    # Info template
    info = self.template()

    # SN
    info['sn'] = data[snOffset:snOffset+snLength].decode("utf-8") 

    # droneLocation
    # 41 -> + 4 bytes [long drone]
    # 45 -> + 4 byes [lat drone]
    info['droneLocation']['lon'] = int.from_bytes(data[41:41+4], byteorder='little') / self.__toDegrees
    info['droneLocation']['lat'] = int.from_bytes(data[45:45+4], byteorder='little') / self.__toDegrees

    # 49 -> + 2 bytes [absolute height]
    # 51 -> + 2 bytes [floor height]
    info['droneLocation']['aHeight'] = int.from_bytes(data[49:49+2], byteorder='little')
    info['droneLocation']['fHeight'] = int.from_bytes(data[51:51+2], byteorder='little') / 10

    # VX, VY, VZ
    info['vx'] = int.from_bytes(data[53:53+2], byteorder='little') / 100
    info['vx'] = int.from_bytes(data[55:55+2], byteorder='little') / 100
    info['vx'] = int.from_bytes(data[57:57+2], byteorder='little') / 100

    # PITCH, ROLL, YAW
    info['pitch'] = int.from_bytes(data[53:53+2], byteorder='little') / (100*57.296)
    info['roll'] = int.from_bytes(data[55:55+2], byteorder='little') / (100*57.296)
    info['yaw'] = int.from_bytes(data[57:57+2], byteorder='little') / (100*57.296)

    # driverLocation
    info['driverLocation']['lon'] = int.from_bytes(data[41:41+4], byteorder='little') / self.__toDegrees
    info['driverLocation']['lat'] = int.from_bytes(data[45:45+4], byteorder='little') / self.__toDegrees

    # homeLocation
    info['homeLocation']['lon'] = int.from_bytes(data[41:41+4], byteorder='little') / self.__toDegrees
    info['homeLocation']['lat'] = int.from_bytes(data[45:45+4], byteorder='little') / self.__toDegrees

    # productId
    info['productId'] = int.from_bytes(data[85:85], byteorder='little', signed=False)

    # uuidLength
    uuidLength = int.from_bytes(data[86:86], byteorder='little', signed=False)
    info['uuid'] = data[86:86+uuidLength].decode("utf-8")

    return info
import requests
import json
import sys
from http import HTTPStatus

# Project imports
from utils import get_logger

logger = get_logger()

# Configuration variables
host = 'http://asdtdev.mooo.com'
detector = '5db1b05fedd685190719f924'
password = 'test'
PORT = 80

# Session variables
token = None

def login(id, password):
  body = { 'id': id, 'password': password}
  response = requests.post(host + '/detector/authenticate', data=body)
  # Get token
  if response.status_code == HTTPStatus.OK:
    response_json = json.loads(response.content.decode()) 
    return response_json['data']['token']
  else:
    return ''
  
  print(response_json)

if __name__ == "__main__":
  logger.info("Login detector with {} / {} ".format(detector, password))
  token = login(detector, password)
  if len(token) == 0:
    logger.error("Login not successful. Aborting")
    sys.exit(0)
  

import jwt
import datetime
import time
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId


# jwt_payload = jwt.encode({
#     'exp': int(time.time()) + 2
# }, 'secret')

# time.sleep(3)
# try:
#   # JWT payload is now expired
#   # But with some leeway, it will still validate
#   token = jwt.decode(jwt_payload, 'secret', leeway=10, algorithms=['HS256'])
#   print(token)
#   print(time.time() > token['exp'])

# except jwt.ExpiredSignatureError:
#   # Signature has expired
#   print("Expired!!!")

# Create MongoClient
client = MongoClient('localhost', 27017)
db = client.asdt
user = db.users.find_one({'_id': ObjectId('5da995c4f67b2d2afcec0c64')})
print(user)
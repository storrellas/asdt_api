import jwt
import datetime
import time
jwt_payload = jwt.encode({
    'exp': int(time.time()) + 2
}, 'secret')

time.sleep(3)
try:
  # JWT payload is now expired
  # But with some leeway, it will still validate
  token = jwt.decode(jwt_payload, 'secret', leeway=10, algorithms=['HS256'])
  print(token)
  print(time.time() > token['exp'])

except jwt.ExpiredSignatureError:
  # Signature has expired
  print("Expired!!!")
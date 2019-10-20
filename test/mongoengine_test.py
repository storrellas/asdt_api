from mongoengine import *
import datetime
import mongoengine

connect('asdt')

class ASDTDocument(Document):
  meta = {'abstract': True}

  # timestamps
  createdAt = DateTimeField()
  updatedAt = DateTimeField(default=datetime.datetime.now)

  # mongooseversion
  mongooseVersion = IntField(db_field="__v")

  def save(self, *args, **kwargs):
      if not self.createdAt:
          self.createdAt = datetime.datetime.now()
      self.updatedAt = datetime.datetime.now()
      self.mongooseVersion = 0
      return super().save(*args, **kwargs)

###############################
# GROUP
###############################



class Group(ASDTDocument):
  meta = {'collection': 'groups'}

  name = StringField(required=True, unique=True, default='')
  parent = ReferenceField("self", reverse_delete_rule = NULLIFY)
  childs = ListField(ReferenceField("self", reverse_delete_rule = NULLIFY))
  users = ListField(LazyReferenceField('Users'), reverse_delete_rule = NULLIFY)


###############################
# DETECTOR
###############################
class DetectorLocation(EmbeddedDocument):
  lat = FloatField(default=41.778443)
  lon = FloatField(default=1.890383)
  height = FloatField(default=10.0)

class Detector(ASDTDocument):
  meta = {'collection': 'detectors'}

  name = StringField(required=True, unique=True, default='')
  password = StringField(required=True, default='')
  location = EmbeddedDocumentField(DetectorLocation)
  groups = ListField(ReferenceField(Group, reverse_delete_rule = NULLIFY))



###############################
# USER
###############################

class UserLocation(EmbeddedDocument):
  lat = FloatField()
  lon = FloatField()

class CircleZoneCenter(EmbeddedDocument):
  longitude = FloatField()
  latitude = FloatField()

class CircleZone(EmbeddedDocument):
  _id = ObjectIdField()
  center = EmbeddedDocumentField(CircleZoneCenter)
  radius = IntField(default=0)
  color = StringField(default='')
  opacity = StringField(default='')
  id = StringField(default='')
  droneID = ListField(StringField())
  visible = BooleanField(default=False)
  active = BooleanField(default=False)

class DisplayOptions(EmbeddedDocument):
  mapType = StringField(default='')
  zone = ListField(ListField(IntField()))
  circleZone = EmbeddedDocumentListField(CircleZone, default=[])

class User(ASDTDocument):
  meta = {'collection': 'users'}

  email = StringField(required=True, unique=True, default='')
  name = StringField(required=True, default='')
  password = StringField(required=True, default='')
  displayOptions = EmbeddedDocumentField(DisplayOptions, default=DisplayOptions())
  location = EmbeddedDocumentField(UserLocation)
  role = StringField(choices=['MASTER', 'ADMIN', 'EMPOWERED', 'VIEWER'], default='ADMIN')
  hasGroup = BooleanField(default=False)
  group = ReferenceField(Group, reverse_delete_rule = NULLIFY)

  # timestamps
  createdAt = DateTimeField()
  updatedAt = DateTimeField(default=datetime.datetime.now)

  # # mongooseversion
  # mongooseVersion = IntField(db_field="__v", default=0)

  # def save(self, *args, **kwargs):
  #     if not self.createdAt:
  #         self.createdAt = datetime.datetime.now()
  #     self.updatedAt = datetime.datetime.now()
  #     return super().save(*args, **kwargs)

# Delete if exists
user = User.objects(email='storrellas@gmail.com')
if user:
  user.delete()

# Create new user
user = User(email='storrellas@gmail.com', 
              name='Sergi', 
              password='Torrellas', 
              displayOptions=DisplayOptions())
user.save()

# Querying all objects
for user in User.objects:
  print(str(user))
  print(user.to_mongo())

# # jwt_payload = jwt.encode({
# #     'exp': int(time.time()) + 2
# # }, 'secret')

# # time.sleep(3)
# # try:
# #   # JWT payload is now expired
# #   # But with some leeway, it will still validate
# #   token = jwt.decode(jwt_payload, 'secret', leeway=10, algorithms=['HS256'])
# #   print(token)
# #   print(time.time() > token['exp'])

# # except jwt.ExpiredSignatureError:
# #   # Signature has expired
# #   print("Expired!!!")

# # Create MongoClient
# client = MongoClient('localhost', 27017)
# db = client.asdt
# user = db.users.find_one({'_id': ObjectId('5da995c4f67b2d2afcec0c64')})
# print(user)
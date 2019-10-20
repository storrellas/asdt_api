

# Mongoengine imports
from mongoengine import *
import datetime


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


class Location(EmbeddedDocument):
  lat = FloatField(default=0.0)
  lon = FloatField(default=0.0)

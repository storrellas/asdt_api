import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asdt_api.settings")

# your imports, e.g. Django models
from user.models import *
from logs.models import *

# Settings does not execute in this manner and we need to recreate connection
import mongoengine
mongoengine.connect('asdt')



# Querying all objects
for item in User.objects:
  print(item.to_mongo())

# Querying all objects
for item in Log.objects:
  print(item.to_mongo())

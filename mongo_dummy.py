import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asdt_api.settings")

# your imports, e.g. Django models
from user.models import *
from logs.models import *
from bson.objectid import ObjectId

from django.conf import settings
# Mongoengine connect
import mongoengine
mongoengine.connect(settings.MONGO_DB, host=settings.MONGO_HOST, port=int(settings.MONGO_PORT))


User.objects.all().delete()
Group.objects.all().delete()
Detector.objects.all().delete()
Inhibitor.objects.all().delete()
Log.objects.all().delete()
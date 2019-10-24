import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asdt_api.settings")

# your imports, e.g. Django models
from user.models import *
from logs.models import *

# Settings does not execute in this manner and we need to recreate connection
import mongoengine
mongoengine.connect('asdt')

# # Querying all objects
# for item in User.objects:
#   print(item.to_mongo())

# # Querying all objects
# for item in Log.objects:
#   print(item.to_mongo())

# # Querying all objects
# for item in Group.objects:
#   print(item.to_mongo())

# Get user
user = User.objects.get(email='a@a.com')

# 1. Print getting allowed detectors for user
##
print("Allowed detectors for user")

# Grab user group
group = user.group

print("GroupId", group.id)
print( "Detectors" )
detector_list_for_user = []
for detector in group.devices.detectors:
  print(detector.fetch().id)
  detector_list_for_user.append( detector.fetch() )


# 2. Getting detectors for Log
##
print("Log detectors - Allowed")

allowed = False
log = Log.objects.get(sn='123')
# for detector in group.devices.detectors:
#   print(detector.fetch().to_mongo())
for detector in log.detectors:
  if detector in detector_list_for_user:
    allowed = True

print("allowed", allowed)

print("Log detectors - NOT Allowed")
allowed = False
log = Log.objects.get(sn='456')
# for detector in group.devices.detectors:
#   print(detector.fetch().to_mongo())
for detector in log.detectors:
  if detector in detector_list_for_user:
    allowed = True

print("allowed", allowed)


# pipeline = [
# {
#   "$project": {
#     "_id": {  "$toString": "$_id" },
#     "dateIni": { "$dateToString": { "format": "%Y-%m-%d", "date": "$dateIni" } },
#     "dateFin": { "$dateToString": { "format": "%Y-%m-%d", "date": "$dateIni" } },
#     "productId": "$productId",
#     "sn": "$sn"
#   }
# }
# ]
# queryset = Log.objects.aggregate(*pipeline)
# #print(queryset.to_json())
# for doc in queryset:
#     print(doc)
#     print(type(doc))

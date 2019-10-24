import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asdt_api.settings")

# your imports, e.g. Django models
from user.models import *
from logs.models import *
from bson.objectid import ObjectId

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

# # 1. Print getting allowed detectors for user
# ##
# print("Allowed detectors for user")

# # Grab user group


# print("GroupId", user.group.id)
# print( "Detectors" )
# detector_list_for_user = []
# for detector in user.group.devices.detectors:
#   print(detector.fetch().id)
#   detector_list_for_user.append( detector.fetch() )


# # 2. Getting detectors for Log
# ##
# print("Log detectors - Allowed")

# allowed = False
# log = Log.objects.get(sn='123')
# # for detector in group.devices.detectors:
# #   print(detector.fetch().to_mongo())
# for detector in log.detectors:
#   if detector in detector_list_for_user:
#     allowed = True

# print("allowed", allowed)

# print("Log detectors - NOT Allowed")
# allowed = False
# log = Log.objects.get(sn='456')
# # for detector in group.devices.detectors:
# #   print(detector.fetch().to_mongo())
# for detector in log.detectors:
#   if detector in detector_list_for_user:
#     allowed = True

# print("allowed", allowed)

# id_list = ['5db15a937b2e4c12421a8af1', '5db15a937b2e4c12421a8af8']
# log_list = Log.objects.filter(id__in=id_list)
# print( len(log_list) )

detector = Detector.objects.first()

log = Log.objects.first()
print("Log1 ID ", log.id)
print("Detectors for log1")
detector_id = ''
# for detector in log.detectors:
#   print(detector.id)
#   detector_id = detector.id
#detector_id = log.detectors[0].id
detector = log.detectors[0]

print("Filtering by detector id", detector_id)

pipeline = [
# {      
#   "$match": { "detectors._id" : { "$in" : [ detector_id ]  } }
# },
{
  "$project": {
    "_id": {  "$toString": "$_id" },
    "dateIni": { "$dateToString": { "format": "%Y-%m-%d", "date": "$dateIni" } },
    "dateFin": { "$dateToString": { "format": "%Y-%m-%d", "date": "$dateIni" } },
    "productId": "$productId",
    "sn": "$sn"
  }
}
]
queryset = Log.objects.aggregate(*pipeline)
#print(queryset.to_json())
for log in queryset:
    print(log)
    print(type(log))


# Printing
print("Directly")
log_list = Log.objects.filter(detectors__in=[detector])
print(len(log_list))
for log in log_list:
  print(log.to_json())



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

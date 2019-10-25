DB_NAME=asdt
COLLECTION_NAME=models
OUTPUT=models.json
mongoexport -d asdt -c models -o models.json

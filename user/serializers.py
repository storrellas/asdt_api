from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=200)
    password = serializers.CharField(max_length=72)
    name = serializers.CharField(max_length=200)
    role = serializers.ChoiceField(choices=['MASTER', 'ADMIN', 'EMPOWERED', 'VIEWER'])
    hasGroup = serializers.BooleanField()
    group = serializers.CharField(max_length=200, required=False)
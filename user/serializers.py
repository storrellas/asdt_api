from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=200, required=False)
    password = serializers.CharField(max_length=72, required=False)
    name = serializers.CharField(max_length=200, required=False)
    role = serializers.ChoiceField(choices=['MASTER', 'ADMIN', 'EMPOWERED', 'VIEWER'], required=False)
    hasGroup = serializers.BooleanField(required=False)
    group = serializers.CharField(max_length=200, required=False)
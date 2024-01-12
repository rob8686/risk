from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    #funds = serializers.PrimaryKeyRelatedField(many=True, queryset=Fund.objects.all())

    class Meta:
        model = User
        fields = ['username', 'password']
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
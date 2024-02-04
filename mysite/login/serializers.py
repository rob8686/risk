from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model. 
    
    """

    class Meta:
        model = User
        fields = ['username', 'password']
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer for JWTs
    
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
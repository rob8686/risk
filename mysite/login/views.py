from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserSerializer, MyTokenObtainPairSerializer
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import viewsets, status
import jwt


class CreateUserView(generics.CreateAPIView):
    """
    A view for creating users.

    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    

class MyTokenObtainPairView(TokenObtainPairView):
    """
    A view for retrieving JWT.
    
    """
    serializer_class = MyTokenObtainPairSerializer


def logoutUser(request):
    """
    Logs out currenbt user.
    
    """
    logout(request)
    return redirect('risk:index')


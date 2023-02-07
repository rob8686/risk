from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenVerifyView
from .views import MyTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

app_name = 'login'

urlpatterns = [
    path('create_account', views.createAccount, name='create_account'),
    path('logout', views.logoutUser, name='logout'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]


from django.urls import path
from . import views

app_name = 'login'

urlpatterns = [
    path('', views.loginUser, name='login'),
    path('create_account', views.createAccount, name='create_account'),
    path('logout', views.logoutUser, name='logout'),
]


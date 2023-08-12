from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
#from mysite.risk.models import Security, Position, Fund
from .. models import Security, Position, Fund
from .. import views
#C:\Users\rheery\PycharmProjects\risk\mysite\risk\models.py
#mysite\risk\models.py
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken
from pymongo import MongoClient

class PositionTests(APITestCase):

    def setUp(self):

        Fund.objects.create(id=200,name='Test Fund',currency='USD',aum=1000000, benchmark='SPY', liquidity_limit='7')
        Security.objects.create(name='Apple Inc.' , ticker='AAPL', sector = 'Technology',industry = 'Consumer Electronics', asset_class = 'EQUITY', currency='USD')
        User.objects.create_user(username='test', email='test_email@test.com', password='test123')

    def test_position(self):
        """
        Test position Post and Get
        """
        #Add authenticaltion tests
        url = reverse('position-list')

        # Test adding a posiiton that is not already in the DB
        data_ttwo = {'security': 'TTWO', 'fund': 200, 'percent_aum': '10'} 
        response_ttwo = self.client.post(url, data_ttwo, format='json')

        # Test adding a posiiton that is already in the DB
        data_aapl = {'security': 'AAPL', 'fund': 200, 'percent_aum': '10'} 
        response_aapl = self.client.post(url, data_aapl, format='json')

        # Test adding a posiiton with an invalid ticker
        data_error = {'security': 'ERROR', 'fund': 200, 'percent_aum': '10'} 
        response_error = self.client.post(url, data_error, format='json')

        self.assertEqual(response_ttwo.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_aapl.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_error.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(url + '?fund=200', format='json')
        json_data = response.json()
        name = json_data[0]['securities']['name']

        # Test that the Get request was successful and there is the correct number of positions and fields
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(json_data), 2)
        self.assertEqual(len(json_data[0]), 11)
        self.assertEqual(name, 'Take-Two Interactive Software, Inc.')


class FundTests(APITestCase):

    def setUp(self):
        test_user = User.objects.create_user(username='test', email='test_email@test.com', password='test123')
        self.access_token = AccessToken.for_user(test_user)

    def test_create_fund(self):
        url = reverse('fund-list')
        data = {'name':'Test Fund','currency':'USD','aum':1000000, 'benchmark':'SPY', 'liquidity_limit':'7'}

        # Test Fund can not be created when user logged out
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test Fund can be created when user logged in
        auth_header = 'Bearer ' + str(self.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=auth_header)
        self.client.login(username="test", password="test123")
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test that the Get request was successful and there is the correct number of funds and fields
        response = self.client.get(url, format='json')
        json_data = response.json()
        name = json_data[0]['name']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(json_data), 1)
        self.assertEqual(len(json_data[0]), 9)
        self.assertEqual(name, 'Test Fund')


class GetRiskDataTests(APITestCase):

    def setUp(self):
        Fund.objects.create(id=201,name='Test 2 Fund',currency='USD',aum=10000000000, benchmark='SPY', liquidity_limit='7')
        url = reverse('position-list')
        data = {'security': 'TTWO', 'fund': 201, 'percent_aum': '10'} 
        self.client.post(url, data, format='json')
        data = {'security': 'AAPL', 'fund': 201, 'percent_aum': '10'} 
        self.client.post(url, data, format='json')
        data = {'security': 'HSBA.L', 'fund': 201, 'percent_aum': '10'} 
        self.client.post(url, data, format='json')
        self.mongo_client = MongoClient('mongodb+srv://robert:BQLUn8C60kwtluCO@risk.g8lv5th.mongodb.net/test')

    def Test_run_risk(self):

        new_db = self.mongo_client.test_db
        collection = new_db.test_collection

        try:
            url = reverse('risk:risk_run' ,args=[201, 'USD'])
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        finally:
            print('HELLO DOT?')


    def test_A_then_B(self):
        self.Test_run_risk()
        liquidity_url = reverse('risk:liquidity' ,args=[201])
        response = self.client.get(liquidity_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        performance_url = reverse('risk:performance' ,args=[201])
        response = self.client.get(performance_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        market_risk_url = reverse('risk:market_risk' ,args=[201])
        response = self.client.get(market_risk_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)




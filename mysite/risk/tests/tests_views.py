from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
#from mysite.risk.models import Security, Position, Fund
from .. models import Security, Position, Fund
#C:\Users\rheery\PycharmProjects\risk\mysite\risk\models.py
#mysite\risk\models.py
from django.contrib.auth.models import User

class PositionTests(APITestCase):

    def setUp(self):

        Fund.objects.create(id=200,name='Test Fund',currency='USD',aum=1000000, benchmark='SPY', liquidity_limit='7')
        #Position.objects.create(security='AAPL', fund=200, percent_aum='10')
        Security.objects.create(name='Apple Inc.' , ticker='AAPL', sector = 'Technology',industry = 'Consumer Electronics', asset_class = 'EQUITY', currency='USD')
        User.objects.create_user(username='test', email='test_email@test.com', password='test123')

    def create_position(self):
        """
        Ensure we can create a new Position object.
        """

        url = reverse('position-list')
        data_ttwo = {'security': 'TTWO', 'fund': 200, 'percent_aum': '10'} 
        response_ttwo = self.client.post(url, data_ttwo, format='json')

        data_aapl = {'security': 'AAPL', 'fund': 200, 'percent_aum': '10'} 
        response_aapl = self.client.post(url, data_aapl, format='json')

        self.assertEqual(response_ttwo.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_aapl.status_code, status.HTTP_201_CREATED)
        #self.assertEqual(Account.objects.count(), 1)
        #self.assertEqual(Account.objects.get().name, 'DabApps')


class FundTests(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(username='test', email='test_email@test.com', password='test123')
        all_users = User.objects.all()
        print('USERS3')
        for user in all_users:
            print(user.username)

    def test_create_fund(self):
        url = reverse('fund-list')
        data = {'name':'Test Fund','currency':'USD','aum':1000000, 'benchmark':'SPY', 'liquidity_limit':'7'}
        all_users = User.objects.all()
        print('USERS1')
        for user in all_users:
            print(user.username)
        login = self.client.login(username="test", password="test123")
        print(login)
        all_users = User.objects.all()
        print('USERS2')
        for user in all_users:
            print(user.username)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)





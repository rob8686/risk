from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .. models import Security, Fund, Benchmark
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken

class PositionTests(APITestCase):
    """
    Tests for position objects.
    """

    def setUp(self):
        """
        Set up for positon test.
        """

        benchmark = Benchmark.objects.create(name='S&P 500',ticker='SPY',currency='USD')
        user = User.objects.create_user(username='test', email='test_email@test.com', password='test123')
        self.access_token = AccessToken.for_user(user)
        Fund.objects.create(id=200,name='Test Fund',currency='USD',aum=1000000, benchmark=benchmark, liquidity_limit='7',owner=user)
        Security.objects.create(name='Apple Inc.' , ticker='AAPL', sector = 'Technology',industry = 'Consumer Electronics', asset_class = 'EQUITY', currency='USD')

    def test_position(self):
        """
        Test position Post and Get.
        """

        #Add authenticaltion tests
        url = reverse('position-list')

        # Test adding a posiiton when not logged in 
        data_ttwo = {'security': 'TTWO', 'fund': 200, 'percent_aum': '10'} 
        response_ttwo = self.client.post(url, data_ttwo, format='json')

        self.assertEqual(response_ttwo.status_code, status.HTTP_401_UNAUTHORIZED)

        auth_header = 'Bearer ' + str(self.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=auth_header)
        self.client.login(username="test", password="test123")

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
    """
    Tests for fund objects.
    """

    def setUp(self):
        """
        Set up for fund test.
        """

        self.test_user = User.objects.create_user(username='test', email='test_email@test.com', password='test123')
        self.access_token = AccessToken.for_user(self.test_user)
        self.benchmark = Benchmark.objects.create(name='S&P 500',ticker='SPY',currency='USD')
        self.access_token = AccessToken.for_user(self.test_user)

    def test_create_fund(self):
        """
        Test fund Post and Get.
        """

        url = reverse('fund-list')
        data = {'name':'Test Fund','currency':'USD','aum':1000000, 'benchmark':1, 'liquidity_limit':'7','owner':1}

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
    """
    Set up for risk data tests.
    """

    def setUp(self):
        benchmark = Benchmark.objects.create(name='S&P 500',ticker='SPY',currency='USD')
        user = User.objects.create_user(username='test', email='test_email@test.com', password='test123')
        Fund.objects.create(name='Test Fund',currency='USD',aum=1000000, benchmark=benchmark, liquidity_limit='7',owner=user)
        self.access_token = AccessToken.for_user(user)
        auth_header = 'Bearer ' + str(self.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=auth_header)
        self.client.login(username="test", password="test123")
        url = reverse('position-list')
        data = {'security': 'TTWO', 'fund': 1, 'percent_aum': '10'} 
        self.client.post(url, data, format='json')
        data = {'security': 'AAPL', 'fund': 1, 'percent_aum': '10'} 
        self.client.post(url, data, format='json')
        data = {'security': 'HSBA.L', 'fund': 1, 'percent_aum': '10'} 
        self.client.post(url, data, format='json')
        self.date = Fund.objects.filter(id=1)[0].last_date


    def test_run_risk(self):
        """
        Test running risk.
        """
        
        url = reverse('risk:risk_run' ,args=[1, 'USD', self.date])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.performance()
        self.liquidity()
        self.market_risk()


    def liquidity(self):
        """
        Test running liquidity.
        """

        url = reverse('risk:liquidity_data' ,args=[1, self.date])
        response = self.client.get(url, format='json')
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['Liquidity_stats'].keys()), 3) # test response is the correct lenght 


    def performance(self):
        """
        Test running performance.
        """

        url = reverse('risk:performance_data' ,args=[1, self.date])
        response = self.client.get(url, format='json')
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data.keys()), 3) # test response is the correct lenght

    def market_risk(self):
        """
        Test running market risk.
        """

        url = reverse('risk:market_risk_data' ,args=[1,self.date])
        response = self.client.get(url, format='json')
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data.keys()), 3) # test response is the correct lenght
















from django.shortcuts import render, redirect
import yfinance as yf
import pandas as pd
from .forms import FundForm, PositionForm, SecurityForm
from .models import Security, Position, Fund
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import viewsets, status
from .serializers import FundSerializer,PositionSerializer, CreatePositionSerializer
from .risk_functions import RefreshPortfolio, GetFx, Performance, Liquidity
from .market_risk import var, Var
from datetime import datetime
from django.db.models import Sum, F
import json
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
# from django.contrib.auth import login, logout, authenticate
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission, SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication
#from urllib.error import HTTPError
from requests.exceptions import HTTPError
from django.db.models import Avg, Count, Sum
client = MongoClient('mongodb+srv://robert:BQLUn8C60kwtluCO@risk.g8lv5th.mongodb.net/test')

class PositionWritePermission(BasePermission):
    message = 'Only user who created the fund can add positions'

    def has_object_permisison(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user == obj.namne
    
    def has_permission(self, request, view):
        user = request.user
        user_name = user.username

        if request.method in SAFE_METHODS:
            return True
        return True

class FundViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication]
    queryset =Fund.objects.all()
    serializer_class = FundSerializer

class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    permission_classes = [PositionWritePermission]

    def get_queryset(self,*args, **kwargs):

        #if there is a fund with the request filter positions for just that fund
        fund = self.request.GET.get('fund')
        if fund:
            return Position.objects.filter(fund=fund)
        return Position.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePositionSerializer
        else: 
            return PositionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) # review
        try:
            self.perform_create(serializer)
        except ValueError:
            return Response('Please enter a valid ticker', status.HTTP_404_NOT_FOUND, template_name=None, headers=None, content_type=None)
        except ZeroDivisionError:
            return Response('Cannot Add Posiiton to fund with zero AUM', status.HTTP_404_NOT_FOUND, template_name=None, headers=None, content_type=None)
        except HTTPError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        headers = self.get_success_headers(serializer.data) # Review
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

 
class GetRiskData(APIView):

    def get(self, request, fund_id, fund_currency,format='json'):

        positions = Position.objects.filter(fund=fund_id).select_related('security') #need this?
        print()
        agg = Position.objects.filter(fund=fund_id).aggregate(Sum("quantity"))
        #.aggregate(sum("qunatity"))
        print(agg)
        print('POsitions')
        print(positions)
        fund = Fund.objects.filter(id=fund_id)[0]
        benchmark = fund.benchmark
        ticker_currency_list = list(positions.values_list("security__ticker","security__currency"))
        benchmark_currency = {'SPY':'USD'}
        
        # get the FX rate df which contains the rates for each unique currency   
        unique_currency_set = set(currency[1] for currency in ticker_currency_list)
        fx_data = GetFx(unique_currency_set,fund_currency)
        fx_data_df = fx_data.get_fx()
        
        # get the unique tickers and request the data from yfinance 
        unique_positions = set(ticker[0] for ticker in ticker_currency_list)
        ticker_string = benchmark + ' ' + ' '.join(unique_positions)
        print(ticker_string)
        data = yf.download(tickers=ticker_string, period="1y",
            interval="1d", group_by='column',auto_adjust=True, prepost=False,threads=True,proxy=None) 
        print('FX Date!!!!!!!!')
        print(data.head())
        #if len(unique_positions) == 1:
            #data.columns = pd.MultiIndex.from_product([data.columns, [ticker_string.split(' ')[0]]])

        # data should not include today
        today = datetime.today().strftime('%Y-%m-%d')
        data[data.index < today]['Close'].fillna(method="ffill").dropna() #inplace??????
        data.index = data.index.strftime('%Y-%m-%d')
        # merge the yfinance df with the fx df
        combined_df = data['Close'].merge(fx_data_df, how='left',left_index=True, right_index=True)
        combined_df = combined_df[combined_df.index < today].fillna(method="ffill").dropna()
        # the rate for the fund currency is 1
        combined_df[fund_currency] = 1
        fx_converted_df = pd.DataFrame()

        # multiply the fx rate by the position closing price to get the FX converted closing price 
        for ticker, ccy in ticker_currency_list:
            combined_df[ticker + '_' + fund_currency] = combined_df[ticker] * combined_df[ccy]
            fx_converted_df[ticker] = combined_df[ticker] * combined_df[ccy]
        fx_converted_df[benchmark] = combined_df[benchmark] * combined_df[benchmark_currency[benchmark]]

        # need to update for CCY!!!!
        refresh = RefreshPortfolio(combined_df,positions)
        refresh.test()

        yf_dict ={}
        yf_dict_2 = {}
        for position in positions:
            sector = position.security.sector
            currency = position.security.currency
            quantity = positions.filter(security__ticker=position).aggregate(Sum("quantity"))['quantity__sum']
            percent_aum = positions.filter(security__ticker=position).aggregate(Sum("percent_aum"))['percent_aum__sum']

            if str(position) in yf_dict:
                yf_dict[str(position)] = [yf_dict[str(position)][0] + position.quantity,yf_dict[str(position)][1] + position.percent_aum, sector, currency]
            else:
                yf_dict[str(position)] = [position.quantity,position.percent_aum, sector, currency]

            yf_dict_2[str(position)] = [quantity, percent_aum, sector, currency]
            print('YF 2""""""""""""""""""""""""""2')
            print(yf_dict_2) 
            print(yf_dict) 
            print()
            
        risk_dict = {}
        performance = Performance(fx_converted_df, yf_dict, benchmark)
        performance_data = performance.get_performance()
        fund.performance_status = performance_data['performance']['pivots']['performance']['status']
        data.drop(columns=[benchmark],inplace=True, level=1)
        liquidity2 = Liquidity(data,yf_dict, fund.liquidity_limit)
        liquidity_data = liquidity2.get_liquidity()
        fund.liquidity_status = liquidity_data['status']
        fund.save()
        client = MongoClient('mongodb+srv://robert:BQLUn8C60kwtluCO@risk.g8lv5th.mongodb.net/test')
        new_db = client.test_db
        new_collection = new_db.test_collection
        var_result = Var(fx_converted_df.drop(benchmark,axis=1), yf_dict, new_collection)
        var_data = var_result.get_var()
        var_result.get_var()
        result2 = new_collection.replace_one({'_id':fund_id},{'text':'Update worked AGAIN!!!!!!','liquidity': liquidity_data, 'performance': performance_data,'market_risk':var_data},upsert=True)
        #var_result = Var(fx_converted_df.drop(benchmark,axis=1), yf_dict, new_collection)
        #print(var_result.get_var())
        var_result.get_var()
        return Response(performance.get_performance(),status=status.HTTP_200_OK)

class GetLiquidity(APIView):
    def get(self, request, fund_id, format='json'):
        db = client.test_db
        collection = db.test_collection
        document = collection.find_one({'_id':fund_id})
        return Response(document["liquidity"],status=status.HTTP_200_OK)

class GetPerformance(APIView):
    def get(self, request, fund_id, format='json'):
        db = client.test_db
        collection = db.test_collection
        document = collection.find_one({'_id':fund_id})
        return Response(document["performance"],status=status.HTTP_200_OK)

class GetMarketRisk(APIView):
    def get(self, request, fund_id, format='json'):
        db = client.test_db
        collection = db.test_collection
        document = collection.find_one({'_id':fund_id})
        return Response(document["market_risk"],status=status.HTTP_200_OK)








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
client = MongoClient('mongodb+srv://robert:BQLUn8C60kwtluCO@risk.g8lv5th.mongodb.net/test')

class PositionWritePermission(BasePermission):
    message = 'Only user who created the fund can add positions'
    print('Only user who created the fund can add positions')

    def has_object_permisison(self, request, view, obj):
        print('hell420')
        print(request)
        print(request.user)
        print('hERE""£$')
        print(request.query_params)
        for i in request:
            print(i)
        print('Finallyyyyyyy?')
        if request.method in SAFE_METHODS:
            return True

        print()
        return request.user == obj.namne
    
    def has_permission(self, request, view):
        print('BLCOKED!!!!!!!')
        print(request)
        print(request.user)
        user = request.user
        user_name = user.username
        print('USERNAME', user_name)
        print(view)
        print(request.data)

        if request.method in SAFE_METHODS:
            return True

        #print(request.query_params.dict()['fund'])
        print()
        print('THEREEEEE')
        print(request.query_params.dict())
        print(request.query_params.dict().keys())
        #fund_id = request.data['fund']
        #print('FUND ID: ', fund_id)
        #fund_name =Fund.objects.get(id=fund_id)
        #print(fund_name)
        #print(fund_name.name)
        print()
        return True

class FundViewSet(viewsets.ModelViewSet):
    print(PositionWritePermission)
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication]
    #permission_classes = [PositionWritePermission]
    queryset =Fund.objects.all()
    serializer_class = FundSerializer

class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    permission_classes = [PositionWritePermission]

    def get_queryset(self,*args, **kwargs):
        fund = self.request.GET.get('fund')
        print(self.request)
        print('HELP "" ** (())')
        print('FUnd',fund)
        if fund:
            return Position.objects.filter(fund=fund)
        return Position.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePositionSerializer
        else : 
            return PositionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except ValueError:
            return Response('Please enter a valid ticker', status.HTTP_404_NOT_FOUND, template_name=None, headers=None, content_type=None)
        except ZeroDivisionError:
            return Response('Cannot Add Posiiton to fund with zero AUM', status.HTTP_404_NOT_FOUND, template_name=None, headers=None, content_type=None)    
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

 
class GetRiskData(APIView):

    def get(self, request, fund_id, fund_currency,format='json'):

        positions = Position.objects.filter(fund=fund_id).select_related('security') #need this?
        fund = Fund.objects.filter(id=fund_id)[0]
        print('FUND NAME!!!!!')
        print(fund.name)
        print(fund.liquidity_limit)
        print('Hello World!')
        print(fund.benchmark)
        benchmark = fund.benchmark
        ticker_currency_quantity = positions.values_list("security__ticker","security__currency","quantity")
        benchmark_currency = {'SPY':'USD'}
        
        unique_currency_set = set(currency[1] for currency in list(ticker_currency_quantity))
        fx_data = GetFx(unique_currency_set,fund_currency)
        fx_data_df = fx_data.combined_fx_data()
        
        unique_positions = set(ticker[0] for ticker in list(ticker_currency_quantity))
        ticker_string = benchmark + ' ' + ' '.join(unique_positions)
        print(ticker_string)
        data = yf.download(tickers=ticker_string, period="1y",
            interval="1d", group_by='column',auto_adjust=True, prepost=False,threads=True,proxy=None) 
        if len(unique_positions) == 1:
            data.columns = pd.MultiIndex.from_product([data.columns, [ticker_string.split(' ')[0]]])

        today = datetime.today().strftime('%Y-%m-%d')
        data[data.index < today]['Close'].fillna(method="ffill").dropna() #inplace??????
        data.index = data.index.strftime('%Y-%m-%d')
        combined_df = data['Close'].merge(fx_data_df, how='left',left_index=True, right_index=True)
        combined_df = combined_df[combined_df.index < today].fillna(method="ffill").dropna()
        combined_df[fund_currency] = 1
        fx_converted_df = pd.DataFrame()

        for ticker, ccy, quantity in ticker_currency_quantity:
            combined_df[ticker + '_' + fund_currency] = combined_df[ticker] * combined_df[ccy]
            fx_converted_df[ticker] = combined_df[ticker] * combined_df[ccy]
        fx_converted_df[benchmark] = combined_df[benchmark] * combined_df[benchmark_currency[benchmark]]

        # need to update for CCY!!!!
        refresh = RefreshPortfolio(combined_df,positions)
        refresh.test()

        yf_dict ={}
        for position in positions:
            sector = position.security.sector
            currency = position.security.currency

            if str(position) in yf_dict:
                yf_dict[str(position)] = [yf_dict[str(position)][0] + position.quantity,yf_dict[str(position)][1] + position.percent_aum, sector, currency]
            else:
                yf_dict[str(position)] = [position.quantity,position.percent_aum, sector, currency]
            
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
        result2 = new_collection.replace_one({'_id':fund_id},{'text':'Update worked AGAIN!!!!!!','liquidity': liquidity_data, 'performance': performance_data},upsert=True)
        var(fx_converted_df, yf_dict)
        var_result = Var(fx_converted_df, yf_dict)
        var_result.position_weights()
        return Response(performance.get_performance())

class GetLiquidity(APIView):
    def get(self, request, fund_id, format='json'):
        db = client.test_db
        collection = db.test_collection
        document = collection.find_one({'_id':fund_id})
        return Response(document["liquidity"])
        #return True

class GetPerformance(APIView):
    def get(self, request, fund_id, format='json'):
        db = client.test_db
        collection = db.test_collection
        document = collection.find_one({'_id':fund_id})
        return Response(document["performance"])
        #return True








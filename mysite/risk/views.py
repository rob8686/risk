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
from .risk_functions import get_yf_data, calc_liquidity, calc_performance, RiskAnalytics, RefreshPortfolio, GetFx, Performance, Liquidity
from datetime import datetime
from django.db.models import Sum, F
import json
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
# from django.contrib.auth import login, logout, authenticate
client = MongoClient('mongodb+srv://robert:BQLUn8C60kwtluCO@risk.g8lv5th.mongodb.net/test')

class FundViewSet(viewsets.ModelViewSet):
    queryset =Fund.objects.all()
    serializer_class = FundSerializer

class PositionViewSet(viewsets.ModelViewSet):
    queryset =Position.objects.all()

    def get_queryset(self,*args, **kwargs):
        fund = self.request.GET.get('fund')
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

    def get(self, request, fund_id, fund_currency, benchmark ,format='json'):

        positions = Position.objects.filter(fund=fund_id).select_related('security') #need this?
        fund = Fund.objects.filter(id=fund_id)
        benchmark = benchmark
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
        data[data.index < today]['Close'].fillna(method="ffill").dropna()
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
        data.drop(columns=[benchmark],inplace=True, level=1)
        liquidity = RiskAnalytics(data,yf_dict)
        liquidity2 = Liquidity(data,yf_dict)
        liquidity2.get_liquidity()
        #client = MongoClient('mongodb+srv://robert:BQLUn8C60kwtluCO@risk.g8lv5th.mongodb.net/test')
        new_db = client.test_db
        new_collection = new_db.test_collection
        result2 = new_collection.replace_one({'_id':fund_id},{'text':'Update worked AGAIN!!!!!!','liquidity': liquidity2.get_liquidity(), 'performance': performance.get_performance()},upsert=True)
        return Response(performance.get_performance())

class GetLiquidity(APIView):
    def get(self, request, fund_id, format='json'):
        db = client.test_db
        collection = db.test_collection
        document = collection.find_one({'_id':fund_id})
        return Response(document["liquidity"])

class GetPerformance(APIView):
    def get(self, request, fund_id, format='json'):
        db = client.test_db
        collection = db.test_collection
        document = collection.find_one({'_id':fund_id})
        return Response(document["performance"])

def index(request):
    fund_list = Fund.objects.all()
    context = {'fund_list': fund_list, 'user': str(request.user)}
    print()
    return render(request, 'risk/index.html', context)


def create(request):
    context = {}

    form = FundForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('risk:index')

    context['form'] = form
    return render(request, "risk/create.html", context)


def position_create(request):
    context = {}

    # make a copy of the post request so it can be altered
    updated_request = request.POST.copy()
    securities = Security.objects.all()
    form = PositionForm(updated_request or None, initial={'quantity': 6667})
    form.fields['fund'].initial = 'ABC UCITS'
    ticker = form['security'].value()

    if request.method == 'POST':

        ticker_list = list((securities.values_list('ticker', flat=True)))

        # If the ticker entered in the form is already an existing Security then change the ticker
        # in the form to the index of the Security in the Security list so the form references
        # a Security object rather than a string. Else set the form value to '0'.
        if ticker in ticker_list:
            updated_request.update({'security': str(ticker_list.index(ticker) + 1)})
        else:
            updated_request.update({'security': '0'})

        # Create Security if doesn't exist
        if int(form['security'].value()) == 0:

            yf_ticker = yf.Ticker(ticker)
            ticker_info = yf_ticker.info

            # check if ticker is valid
            if len(ticker_info) > 3:
                security = Security.objects.create(
                    name=ticker_info['longName'], ticker=ticker, 
                    sector=ticker_info['sector'],industry=ticker_info['industry'],
                    asset_class=ticker_info['quoteType'], currency=ticker_info['currency'])
                    
                ticker_list = list((securities.values_list('ticker', flat=True)))
                updated_request.update({'security': str(ticker_list.index(ticker) + 1)})


        if form.is_valid():
            instance = form.save(commit=False)
            closing_price = yf.Ticker(ticker).history(period="1d")['Close']
            closing_price.index = closing_price.index.strftime('%Y/%m/%d')
            instance.last_price = closing_price.item()
            instance.price_date = datetime.strptime(closing_price.index[0],'%Y/%m/%d')
            form.save()
            return redirect('risk:index')

    context['form'] = form

    return render(request, "risk/position_create.html", context)


def security_create(request):
    context = {}

    form = SecurityForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('risk:index')

    context['form'] = form
    return render(request, "risk/security_create.html", context)


def fund_positions(request, fund_name):
    positions = Position.objects.filter(fund__name=fund_name)
    context = {'fund_positions': positions}
    return render(request, "risk/fund_positions.html", context)


@api_view(['GET'])
def get_hist_data_REST(request):
    #print(fund_name)
    #positions = Position.objects.filter(fund__name=fund_name)
    # fund = Fund.objects.filter(name=fund_name)
    # print(fund[0].Positions.all())
    #ticker_string = ''
    #for position in positions:
    #    print(position)
    #    ticker_string = ticker_string + str(position) + ' '

    request.session.set_expiry(0)
    #print('Ticker String')
    #print(ticker_string)
    #yf_data = get_yf_data(ticker_string)
    #print(yf_data)
    #request.session[fund_name] = yf_data.to_json(orient="split")
    # request.session['fav_color'] = 'blue'
    # print(request.session['fav_color'])
    #print(request.session[fund_name])
    #context = {'hist_data': request.session[fund_name]}
    # return render(request, "risk/get_hist_data.html", context)

    funds = Fund.objects.all()
    serializer = FundSerializer(funds, many=True)
    return Response(serializer.data)

    #return Response(context)

def get_hist_data(request, fund_name):
    positions = Position.objects.filter(fund__name=fund_name)
    #print(list(positions.values_list('quantity', flat=True))) 
    if positions.count() > 0:
        ticker_string = ''
        position_dict = {}

        for position in positions:
            position_dict[str(position)] = [position.quantity]
            ticker_string = ticker_string + str(position) + ' '

        request.session.set_expiry(0)

        yf_data = get_yf_data(ticker_string)
        yf_data.index = yf_data.index.strftime('%Y-%m-%d')

        performance = calc_performance(yf_data['Close'])
        print(performance)

        average_volumne = yf_data['Volume'].reset_index().mean().to_dict()
        
        for position in positions:
            ticker_series = yf_data['Close'][str(position)]
            last_price_index = ticker_series.last_valid_index()
            last_price_loc = ticker_series.index.get_loc(last_price_index)
            position.last_price = ticker_series[last_price_loc]
            position.price_date = datetime.strptime(last_price_index,'%Y-%m-%d')
            position.save()

        for ticker in average_volumne:
            if positions.count() > 1:
                position_dict[ticker].append(average_volumne[ticker])
            else:
                position_dict[ticker_string.strip()].append(average_volumne[ticker])

        liquidity_dict = {}
        for ticker in position_dict:
            quantity = float(position_dict[ticker][0])
            adv = float(position_dict[ticker][1])
            liquidity_dict[ticker] = calc_liquidity(quantity,adv) 
        
        context = {'hist_data': liquidity_dict}

        #request.session[fund_name] = '{"closing":' + yf_data['Close'].to_json(orient="split") +\
        #', "volume":' + yf_data['Volume'].to_json(orient="split") + '}'

        return render(request, "risk/get_hist_data.html", context)

    else:
        return redirect('risk:index')


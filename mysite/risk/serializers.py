from rest_framework import serializers
from .models import Fund, Position, Security
import yfinance as yf
import datetime
import math
from .risk_functions import GetFx


class FundSerializer(serializers.ModelSerializer):

    last_date = serializers.CharField(read_only=True)

    class Meta:
        model = Fund
        fields = '__all__'
        #read_only_fields = ('last_date',)

class SecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Security
        fields = '__all__'

class PositionSerializer(serializers.ModelSerializer):

    securities = SecuritySerializer(source='security', read_only=True)

    class Meta:
        model = Position
        fields = '__all__'
        #depth = 1
 
class CreatePositionSerializer(serializers.ModelSerializer):

    fund = serializers.CharField()
    security = serializers.CharField()

    class Meta:
        model = Position
        fields = ('quantity', 'security','fund','percent_aum')

    def create(self, validated_data):
        ticker = validated_data['security']
        fund = validated_data['fund']
        securities = Security.objects.filter(ticker=ticker)
        security_currency = securities[0].currency
        funds = Fund.objects.filter(pk=fund)
        fund_currency = funds[0].currency
        print('FUnd Currency')
        print(fund_currency)
        validated_data['fund'] = funds.first()
        
        if securities.first():
            validated_data['security'] = securities.first()
        else:
            yf_ticker = yf.Ticker(ticker)
            ticker_info = yf_ticker.info

            if len(ticker_info) > 3:
                new_security = Security.objects.create(
                    name=ticker_info['longName'], ticker=ticker, 
                    sector=ticker_info['sector'],industry=ticker_info['industry'],
                    asset_class=ticker_info['quoteType'], currency=ticker_info['currency'])

        if isinstance(validated_data['security'], Security):
            closing_price = yf.Ticker(ticker).history(period="1d")['Close']
            closing_price.index = closing_price.index.strftime('%Y/%m/%d')
            validated_data['last_price'] = closing_price.item()
            validated_data['price_date'] = datetime.datetime.strptime(closing_price.index[0],'%Y/%m/%d').strftime('%Y-%m-%d')
            get_fx = GetFx([security_currency],fund_currency)
            fx_rate = get_fx.get_fx(security_currency,validated_data['price_date'])
            validated_data['fx_rate'] = fx_rate    
            validated_data['quantity'] = math.floor((validated_data['percent_aum'] * funds[0].aum / 100) / closing_price / float(fx_rate))
            validated_data['mkt_value_local'] = validated_data['last_price'] * validated_data['quantity']
            validated_data['mkt_value_base'] = validated_data['mkt_value_local'] * float(fx_rate) 
            validated_data['percent_aum'] = validated_data['mkt_value_base'] / funds[0].aum


        obj = Position.objects.create(**validated_data)

        return obj       

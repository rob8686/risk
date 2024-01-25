from rest_framework import serializers
from .models import Fund, Position, Security, PerformanceHistory, PerformancePivots, LiquditiyResult, FxData
import yfinance as yf
import datetime
import math
from .risk_functions import GetFx


class FundSerializer(serializers.ModelSerializer):
    """
    Serializer for the Fund model. Includes last price parameter.
    """

    last_date = serializers.CharField(read_only=True)

    class Meta:
        model = Fund
        fields = '__all__'

class SecuritySerializer(serializers.ModelSerializer):
    """
    Serializer for the Security model. 
    """
     
    class Meta:
        model = Security
        fields = '__all__'

class PositionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Position model.
    """

    securities = SecuritySerializer(source='security', read_only=True)

    class Meta:
        model = Position
        fields = '__all__'
 
class CreatePositionSerializer(serializers.ModelSerializer):
    """
    Serializer for creating instances of the Position model.
    """

    fund = serializers.CharField()
    security = serializers.CharField()

    class Meta:
        model = Position
        fields = ('security','fund','percent_aum')

    def create(self, validated_data):
        """
        Creates a position instance. 
        If the related security already exists use that or else use create a new security object.
        """

        # filter Fund and Security objects by the data provided
        # then replace the security and fund strings the returned objects  
        ticker = validated_data['security']
        fund = validated_data['fund']
        securities = Security.objects.filter(ticker=ticker)
        funds = Fund.objects.filter(pk=fund)
        fund_currency = funds[0].currency
        validated_data['fund'] = funds.first()
        # If the security is already in the DB use it
        if securities.first():
            validated_data['security'] = securities.first()
            security_currency = securities[0].currency
        # else download the security data from yfinance and create a new Security    
        else:
            yf_ticker = yf.Ticker(ticker)
            ticker_info = yf_ticker.info
            if ticker_info['quoteType'] == 'ETF':
                sector, industry  = 'ETF', 'ETF'
            else:
                sector, industry = ticker_info['sector'], industry=ticker_info['industry']
                
            # this is the lenght of an empty response
            if len(ticker_info) > 3:
                security = Security.objects.create(
                    name=ticker_info['longName'], ticker=ticker, 
                    asset_class=ticker_info['quoteType'], currency=ticker_info['currency'],
                    sector=sector,industry=industry)
                
                security_currency = ticker_info['currency']
                validated_data['security'] =  security
        # add the remaining Position fields to the data 
        if isinstance(validated_data['security'], Security):
            closing_price = yf.Ticker(ticker).history(period="1d")['Close']
            closing_price.index = closing_price.index.strftime('%Y/%m/%d')
            validated_data['last_price'] = closing_price.item()
            validated_data['price_date'] = datetime.datetime.strptime(closing_price.index[0],'%Y/%m/%d').strftime('%Y-%m-%d')
            if fund_currency != security_currency:
                get_fx = GetFx([security_currency],fund_currency,FxData)
                fx_rate = get_fx.get_fx(validated_data['price_date'])
            else:
                fx_rate = 1
            validated_data['fx_rate'] = fx_rate    
            validated_data['quantity'] = math.floor((validated_data['percent_aum'] * funds[0].aum / 100) / closing_price / float(fx_rate))
            validated_data['mkt_value_local'] = validated_data['last_price'] * validated_data['quantity']
            validated_data['mkt_value_base'] = validated_data['mkt_value_local'] * float(fx_rate) 
            validated_data['percent_aum'] = validated_data['mkt_value_base'] / funds[0].aum
        obj = Position.objects.create(**validated_data)
        return obj       






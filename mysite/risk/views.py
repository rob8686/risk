from django.shortcuts import render, redirect
from .models import Position, Fund, PerformanceHistory, PerformancePivots, LiquditiyResult, MarketRiskStatistics, MarketRiskCorrelation, HistogramBins, HistVarSeries
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import viewsets, status
from .serializers import FundSerializer,PositionSerializer, CreatePositionSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission, SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication
from requests.exceptions import HTTPError
from django.contrib.auth.models import User
import json

class PositionWritePermission(BasePermission):
    """
    Object-level permission to only allow the fund owner to add or delete positions.
    """

    message = 'Only user who created the fund can add / delete positions'

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        print('DELETE USER')
        print(request.user)
        print(obj.fund.owner)
        return request.user == obj.fund.owner


class FundViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing funds.

    Provides CRUD operations (Create, Read, Update, Delete) for the Fund model.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication]
    queryset = Fund.objects.all()
    serializer_class = FundSerializer


class PositionViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing positions.
    
    Provides CRUD operations (Create, Read, Update, Delete) for the Position model.
    """
    queryset = Position.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [PositionWritePermission]

    def get_queryset(self,*args, **kwargs):
        """
        Overrides get_queryset to filter the queryset for the related fund.
        """
        fund = self.request.GET.get('fund')
        if fund:
            return Position.objects.filter(fund=fund)
        return Position.objects.all()

    def get_serializer_class(self):
        """
        Overrides get_serializer_class to return a serializer based on the request type.
        """
        if self.action == 'create':
            return CreatePositionSerializer
        else: 
            return PositionSerializer

    def create(self, request, *args, **kwargs):
        """
        Overrides create to include custom permissions and error handling.
        """

        # only allow the fund ownwe to create a position in a fund
        fund_id = json.loads(request.body.decode('utf-8'))['fund']
        fund_owner = Fund.objects.filter(id=fund_id)[0].owner

        if request.user != fund_owner:
            return Response('Only fund owner can create positions.', status.HTTP_401_UNAUTHORIZED, template_name=None, headers=None, content_type=None)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
        except ValueError:
            return Response('Please enter a valid ticker', status.HTTP_404_NOT_FOUND, template_name=None, headers=None, content_type=None)
        except ZeroDivisionError:
            return Response('Cannot Add Posiiton to fund with zero AUM', status.HTTP_404_NOT_FOUND, template_name=None, headers=None, content_type=None)
        except HTTPError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        headers = self.get_success_headers(serializer.data) # Review!!!!!!!!!!!!
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

class PerformanceAPIView(APIView):
    """
    API view for returning fund performance data.
    """

    def get(self, request, fund_id, date):
        """
        Gets: 
        - fund and benchamrk price timeseries
        - fund statistics such as return, volatility and sharpe ratio
        - performance pivoted by currency and industry 
        - the performance status of the fund (pass / warning / fail) 
        """

        performance_history = PerformanceHistory.objects.filter(fund__pk=fund_id).filter(as_of_date=date).values('date', 'fund_history', 'benchamrk_history')
        performance_pivots = PerformancePivots.objects.performance_stats(fund_id)
        performance_stats = PerformanceHistory.objects.performance_stats(fund_id)
        return Response({'performance_pivots': performance_pivots,'performance_history':performance_history,'performance_stats':performance_stats},status=status.HTTP_200_OK)
    

class LiquidityResultAPIView(APIView):
    """
    API view for returning fund liquidity data.
    """
     
    def get(self, request, fund_id, date):
        """
        Gets: 
        - time to liqudiate for fund and psoitions 
        - the liquidity status of the fund
        """
        Liquidity_stats = LiquditiyResult.objects.liquidity_stats(fund_id)
        return Response({'Liquidity_stats':Liquidity_stats},status=status.HTTP_200_OK)
    

class MarketRiskResultAPIView(APIView):
    """
    API view for returning market risk data.
    """

    def get(self, request, fund_id, date):
        """
        Gets: 
        - VaR history
        - Factor VaR and stress testing results
        - Parametric VaR result and statistics
        """
        hist_var_history = HistVarSeries.objects.filter(fund__pk=fund_id).filter(as_of_date=date).values('date', 'pl')
        risk_stats = MarketRiskStatistics.objects.filter(fund__pk=fund_id).filter(as_of_date=date)
        var_1d_hist = risk_stats.filter(type='hist_var_result')[0].value
        var_1d_parametric = risk_stats.filter(type='parametric_var')[0].value
        histogram = HistogramBins.objects.filter(fund__pk=fund_id).filter(as_of_date=date).values('bin','count')
        correlation_data = MarketRiskCorrelation.objects.get_correlation(fund_id)
        tickers, correlation_matrix = correlation_data[0], correlation_data[1]
        stress_tests = risk_stats.filter(catagory='stress_test').values('type','value')

        print('CORRELATION')
        print(correlation_matrix)
        print('var_1d_parametric')
        print(var_1d_parametric)



        return Response({
            'factor_var': {'historical_data':hist_var_history, 'var_1d':var_1d_hist},
            'stress_tests':stress_tests, 
            'parametric_var':{'var_1d':var_1d_parametric,'histogram':histogram, 'tickers':tickers,'correlation':correlation_matrix}},
            status=status.HTTP_200_OK
            )
    

class GetRiskData(APIView):
    """
    API view that runs the risk calcualtions.
    """

    def get(self, request, fund_id, fund_currency,date, format='json'):
        """
        RUn risk calcualtions for inputed fund.
        """ 

        fund = Fund.objects.filter(id=fund_id)[0]
        fund.run_risk(date)
        return Response(status=status.HTTP_200_OK)

        
class TestView(APIView):
    def get(self, request):
        fund_id = 1
        run_risk = RuntimeError(fund_id)
        run_risk.run_risk()
        return Response('HELLO',status=status.HTTP_200_OK)








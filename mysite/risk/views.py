from django.shortcuts import render, redirect
from .models import Position, Fund, PerformanceHistory, PerformancePivots, LiquditiyResult, MarketRiskStatistics, MarketRiskCorrelation, HistogramBins, HistVarSeries
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import viewsets, status
from .serializers import FundSerializer,PositionSerializer, CreatePositionSerializer, PerformanceHistorySerializer, PerformancePivotSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission, SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication
from requests.exceptions import HTTPError


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
    permission_classes = [PositionWritePermission]

    def get_queryset(self,*args, **kwargs):
        """
        Overrides get_queryset to filter the queryset for the related fund.
        """

        #if there is a fund with the request filter positions for just that fund
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

class PerformanceHistoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication]
    queryset = PerformanceHistory.objects.all()
    serializer_class = PerformanceHistorySerializer

    def get_queryset(self):
        fund = self.request.GET.get('fund')
        queryset = PerformanceHistory.objects.filter(fund__pk=fund)
        return queryset
    

    def list(self, requests):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        performance_stats = PerformanceHistory.objects.performance_stats()
        response_data = {
            'data': serializer.data,
            'performance_stats': performance_stats
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
class PerformancePivotViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication]
    queryset = PerformancePivots.objects.all()
    serializer_class = PerformancePivotSerializer
    
    def get_queryset(self):
        fund = self.request.GET.get('fund')
        queryset = PerformancePivots.objects.filter(fund__pk=fund)
        return queryset
    

class PerformanceAPIView(APIView):
    def get(self, request, fund_id):
        performance_history = PerformanceHistory.objects.filter(fund__pk=fund_id).values('date', 'fund_history', 'benchamrk_history')
        performance_pivots = PerformancePivots.objects.performance_stats(fund_id)
        performance_stats = PerformanceHistory.objects.performance_stats(fund_id)

        return Response({'performance_pivots': performance_pivots,'performance_history':performance_history,'performance_stats':performance_stats},status=status.HTTP_200_OK)
    
class LiquidityResultAPIView(APIView):
    def get(self, request, fund_id):
        Liquidity_stats = LiquditiyResult.objects.liquidity_stats(fund_id)
        return Response({'Liquidity_stats':Liquidity_stats},status=status.HTTP_200_OK)
    
class MarketRiskResultAPIView(APIView):
    def get(self, request, fund_id):
        hist_var_history = HistVarSeries.objects.filter(fund__pk=fund_id).values('date', 'pl')
        risk_stats = MarketRiskStatistics.objects.filter(fund__pk=fund_id)
        var_1d_hist = risk_stats.filter(type='hist_var_result')[0].value
        var_1d_parametric = risk_stats.filter(type='parametric_var')[0].value
        histogram = HistogramBins.objects.filter(fund__pk=fund_id).values('bin','count')
        correlation_data = MarketRiskCorrelation.objects.get_correlation(fund_id)
        tickers, correlation_matrix = correlation_data[0], correlation_data[1]
        stress_tests = risk_stats.filter(catagory='stress_test').values('type','value')

        return Response({
            'factor_var': {'historical_data':hist_var_history, 'var_1d':var_1d_hist},
            'stress_tests':stress_tests, 
            'parametric_var':{'var_1d':var_1d_parametric,'histogram':histogram, 'tickers':tickers,'correlation':correlation_matrix}},
            status=status.HTTP_200_OK
            )
    

class GetRiskData(APIView):
    def get(self, request, fund_id, fund_currency,format='json'):

            fund = Fund.objects.filter(id=fund_id)[0]
            fund.run_risk()
            return Response(status=status.HTTP_200_OK)

        

class TestView(APIView):
    def get(self, request):
        fund_id = 1
        run_risk = RuntimeError(fund_id)
        run_risk.run_risk()
        return Response('HELLO',status=status.HTTP_200_OK)








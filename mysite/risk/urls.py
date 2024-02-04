from django.urls import path
from . import views

app_name = "risk"

urlpatterns = [
    path('api/risk_data/<int:fund_id>/<str:fund_currency>/<str:date>', views.GetRiskData.as_view(), name='risk_run'),
    path('api/test_view/', views.TestView.as_view(),name='test_view'),
    path('api/performance_data/<int:fund_id>', views.PerformanceAPIView.as_view(),name='performance_data'),
    path('api/liquidity_data/<int:fund_id>', views.LiquidityResultAPIView.as_view(),name='liquidity_data'),
    path('api/market_risk_data/<int:fund_id>', views.MarketRiskResultAPIView.as_view(),name='market_risk_view'),
]
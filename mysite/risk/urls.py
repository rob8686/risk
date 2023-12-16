from django.urls import path
from . import views

app_name = "risk"

urlpatterns = [
    path('api/risk_data/<int:fund_id>/<str:fund_currency>/', views.GetRiskData.as_view(), name='risk_run'),
    path('api/liquidity/<int:fund_id>', views.GetLiquidity.as_view(), name='liquidity'),
    path('api/performance/<int:fund_id>', views.GetPerformance.as_view(),name='performance'),
    path('api/market_risk/<int:fund_id>', views.GetMarketRisk.as_view(),name='market_risk'),
    path('api/test_view/', views.TestView.as_view(),name='test_view'),
    path('api/performance_data/', views.PerformanceAPIView.as_view(),name='test_view'),
]
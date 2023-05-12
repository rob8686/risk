from django.urls import path
from . import views

app_name = "risk"

urlpatterns = [
    path('api/risk_data/<int:fund_id>/<str:fund_currency>/', views.GetRiskData.as_view()),
    path('api/liquidity/<int:fund_id>', views.GetLiquidity.as_view()),
    path('api/performance/<int:fund_id>', views.GetPerformance.as_view()),
]
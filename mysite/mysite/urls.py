from django.contrib import admin
from django.urls import include, path
from django.contrib import admin
from django.urls import path
from .router import router

urlpatterns = [
    path('', include('frontend.urls')),
    path('risk/', include('risk.urls')),
    path('login/', include('login.urls')),
    path('admin/', admin.site.urls),
    path('api/',include(router.urls)),
    #path('api/risk_data', risk.views.RiskViewSet.as_view(), name='example')
    #path('', include('frontend.urls'))
]

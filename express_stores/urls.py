"""express_stores URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Store import views as store_views
from Sync import views as sync_views
from Stocks import custom_admin as stocks_custom_admin
from express_stores.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('store/sendotp', store_views.sendOTP),
    path('store/login', store_views.login),
    path('sync/getsync', sync_views.syncBackend),
    path('sync/postsync', sync_views.syncClientData),
    path('custom_admin/request_stock/status_change', stocks_custom_admin.StockItemStatus),
    path('custom_admin/request_stock/col_change', stocks_custom_admin.StockItemChange)
]

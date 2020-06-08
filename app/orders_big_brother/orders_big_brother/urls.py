"""orders_big_brother URL Configuration

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

from . import views as base_views

# connect_path = path(
#     r'connect',
#     base_views.ConnectView.as_view(),
#     name='connect',
# )
#
# home_path = path(
#     r'',
#     base_views.HomePageView.as_view(),
#     name='home',
# )
#
# install_path = path(
#     r'install',
#     base_views.InstallView.as_view(),
#     name='install',
# )

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', base_views.login, name='shopify_app_login'),
    path('install', base_views.authenticate, name='shopify_app_authenticate'),
    path('connect', base_views.finalize, name='shopify_app_login_finalize'),
    path('logout/', base_views.logout, name='shopify_app_logout'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.signup_view, name='signup'),
    path('verify/', views.verify_view, name='verify'),
    path('signin/', views.signin_view, name='signin'),
    path('logout/', views.logout_view, name='logout'),
    path('display/', views.display_view, name='display'),
    path('mobile/', views.mobile_view, name='mobile_view'),
    path('competitor-prices/<str:productid>/', views.competitor_prices, name='competitor_prices'),
    path('add-product/', views.add_product_view, name='add_product'),

]
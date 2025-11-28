from django.urls import path
from . import views

urlpatterns = [
    path('', views.signup_view, name='signup'),
    path('verify/<str:email>/', views.verify_view, name='verify'),
    path('resend/<str:email>/', views.resend_code_view, name='resend_code'),
    path('signin/', views.signin_view, name='signin'),
    path('logout/', views.logout_view, name='logout'),
    path('display/', views.display_view, name='display'),
    path('mobile/', views.mobile_view, name='mobile_view'),
    path('competitor_prices/<str:productid>/', views.competitor_prices, name='competitor_prices'),
    path('search/', views.search_products, name='search_products'),
    path('add-product/', views.add_product_view, name='add_product'),
    path('logout_view/', views.logout_view, name='logout_view'),
    path('compare_products/', views.compare_products, name='compare_products'),
    path('products/', views.product_list_view, name='product_list'),
    path('products/<str:category>/<str:productid>/edit/', views.edit_product_view, name='edit_product'),
    path('products/<str:category>/<str:productid>/delete/',views.delete_product_view, name='delete_product'),
    path('reviews/', views.review_page, name="review_page"),
    path('reviews/<str:category>/<str:productid>/add/', views.add_review, name="add_review"),

]
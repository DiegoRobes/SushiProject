from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views as v

urlpatterns = [
    path('', v.home, name="home"),
    path('details/<slug:slug>', v.details, name="details"),
    path('about', v.about, name="about"),
    path('cart', v.cart, name="cart"),
    path('checkout', v.checkout, name="checkout"),
]

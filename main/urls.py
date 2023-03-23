from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views as v

urlpatterns = [
    path('', v.home, name="home"),
    path('details/<slug:slug>', v.details, name="details"),
    path('about', v.about, name="about"),
    path('welcome', v.welcome, name="welcome"),
    path('sign_up', v.sign_up, name="sign_up"),
    path('login/', v.login_user, name="login"),
    path('logout', v.logout_user, name="logout"),
    path('cart', v.cart, name="cart"),
    path('checkout', v.checkout, name="checkout"),
    path('dashboard', v.dashboard, name="dashboard"),
    path('update_item', v.update_item, name="update_item"),
]

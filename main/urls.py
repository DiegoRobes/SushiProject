from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views as v

urlpatterns = [
    path('', v.home, name="home"),
    path('details/<slug:slug>', v.details, name="details"),
    path('added-to-cart', v.added_to_cart, name='added-to-cart'),
    path('about', v.about, name="about"),
    path('welcome', v.welcome, name="welcome"),
    path('sign_up', v.sign_up, name="sign_up"),
    path('login/', v.login_user, name="login"),
    path('logout', v.logout_user, name="logout"),
    path('cart', v.cart, name="cart"),
    path('checkout', v.checkout, name="checkout"),
    path('set_address', v.set_address, name='set_address'),
    path('dashboard', v.dashboard, name="dashboard"),
    path('delete_address', v.delete_address, name="delete_address"),
    path('update_item', v.update_item, name="update_item"),
    path('process_order', v.process_order, name='process_order'),
]

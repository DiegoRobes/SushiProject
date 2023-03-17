from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from . import models as m
from . import forms as f
from django.contrib.auth.models import User


# Create your views here.
def home(request):
    featured = m.Product.objects.filter(featured=True)[0]

    entry_tag = m.Tag.objects.filter(slug='entry')[0]
    entries = m.Product.objects.filter(tag=entry_tag)

    soup_tag = m.Tag.objects.filter(slug='soup')[0]
    soups = m.Product.objects.filter(tag=soup_tag)

    main_tag = m.Tag.objects.filter(slug='main')[0]
    mains = m.Product.objects.filter(tag=main_tag)

    dessert_tag = m.Tag.objects.filter(slug='dessert')[0]
    desserts = m.Product.objects.filter(tag=dessert_tag)

    refreshment_tag = m.Tag.objects.filter(slug='refreshment')[0]
    refreshments = m.Product.objects.filter(tag=refreshment_tag)

    context = {'featured': featured,
               'entries': entries,
               'soups': soups,
               'mains': mains,
               'desserts': desserts,
               'refreshments': refreshments}

    return render(request, "main/index.html", context=context)


def welcome(request):
    context = {}
    return render(request, "main/welcome.html", context=context)


def sign_up(request):
    form = f.CustomerRegistration
    if request.POST:
        register_form = f.CustomerRegistration(request.POST)
        if register_form.is_valid():
            register_form.save()
            request.session['subscribe'] = True
            context = {}
            return HttpResponseRedirect(reverse('dashboard'))
    context = {'form': form}
    return render(request, "main/sign_up.html", context=context)


def login(request):
    context = {}
    return render(request, "main/login.html", context=context)


def dashboard(request):
    context = {}
    return render(request, "main/dashboard.html", context=context)


def details(request, slug):
    selected = m.Product.objects.get(slug=slug)
    context = {'selected': selected}
    return render(request, "main/details.html", context=context)


def about(request):
    context = {}
    return render(request, "main/about.html", context=context)


def cart(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
    else:
        items = []
    context = {'items': items}
    return render(request, "main/cart.html", context=context)


def checkout(request):
    context = {}
    return render(request, "main/checkout.html", context=context)

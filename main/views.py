import json
from . import forms as f
from . import models as m
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse


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

    if request.user.is_authenticated:
        customer = request.user
        # here we create or get the order, and find one that matches the customer in turn and is also open
        order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
        # then get the items of this particular order and send them to the context dict
        items = order.orderitem_set.all()
        context['items'] = items
        # finally we gather the whole order, in order to use the get methods for total prices and quantities
        context['order'] = order

    return render(request, "main/index.html", context=context)


def welcome(request):
    context = {}
    return render(request, "main/welcome.html", context=context)


# get the register form and send it into the template via context.
# if the method is request and the validation is complete, we can create and save a User into the db just as
# easy as that
def sign_up(request):
    register_form = f.RegisterForm()
    shipping_form = f.ShippingForm()
    context = {'register_form': register_form, 'shipping_form': shipping_form}
    if request.POST:
        register_form = f.RegisterForm(request.POST)
        shipping_form = f.ShippingForm(request.POST)
        if register_form.is_valid():
            user = register_form.save()
            login(request, user)
        return redirect(reverse('dashboard'))
    return render(request, "registration/sign_up.html", context=context)


def login_user(request):
    context = {}
    if request.POST:
        pass

    return render(request, "registration/login.html", context=context)


def dashboard(request):
    context = {}
    return render(request, "main/dashboard.html", context=context)


def details(request, slug):
    context = {}
    try:
        selected = m.Product.objects.get(slug=slug)
        context = {'selected': selected}
    except Exception as e:
        print(e)
    return render(request, "main/details.html", context=context)


def about(request):
    context = {}
    return render(request, "main/about.html", context=context)


def cart(request):
    # if the user is auth, then we get the customer linked to them
    context = {}
    if request.user.is_authenticated:
        customer = request.user
        # here we create or get the order, and find one that matches the customer in turn and is also open
        order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
        # then get the items of this particular order and send them to the context dict
        items = order.orderitem_set.all()
        context['items'] = items
        # finally we gather the whole order, in order to use the get methods for total prices and quantities
        context['order'] = order

    return render(request, "main/cart.html", context=context)


def checkout(request):
    context = {}
    if request.user.is_authenticated:
        customer = request.user
        # here we create or get the order, and find one that matches the customer in turn and is also open
        order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
        # then get the items of this particular order and send them to the context dict
        items = order.orderitem_set.all()
        context['items'] = items
        # finally we gather the whole order, in order to use the get methods for total prices and quantities
        context['order'] = order
    return render(request, "main/checkout.html", context=context)


# once the request is passed using the js function on the other side, we can access the request dictionary
# and its contents. check the (request.body), it is accessing the key of body from that dict
# then we return a response that will be rendered by the js function, in the form of a json
def update_item(request):
    data = json.loads(request.body)
    product_id = data['product_id']
    action = data['action']
    # once the request dict is here, we begin to create the order proper. for that, first we get the user. check that
    # var in base template. then get the id from the dictionary to get the right object from the db
    # after that we create a variable that contains an order and assign the customer to that order
    # then the same with an OrderItem variable. using the dictionary contents to link the OrderItem to the right
    # product and order.
    # remember, the orderitems we create here will only be added the order of a logged-in user.
    # so if the user is not logged, nothing will happen to the cart
    customer = request.user
    product = m.Product.objects.get(id=product_id)
    order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = m.OrderItem.objects.get_or_create(order=order, product=product)

    # then we check what the action is and see what to do. then save the orderItem object to the db
    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1
    orderItem.save()

    if action == 'delete' or orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('item added to the cart', safe=False)

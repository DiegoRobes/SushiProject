import json
import datetime
from . import forms as f
from . import models as m
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
# stripe imports
import stripe
from django.conf import settings
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def home(request):
    if 'shopping_data' not in request.session:
        request.session['shopping_data'] = []

    print(request.session['shopping_data'])
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


def about(request):
    context = {}
    return render(request, "main/about.html", context=context)


def welcome(request):
    context = {}
    if request.user.is_authenticated:
        return redirect(reverse('dashboard'))
    else:
        return render(request, "main/welcome.html", context=context)


# get the register form and send it into the template via context.
# if the method is request and the validation is complete, we can create and save a User into the db just as
# easy as that
def sign_up(request):
    if request.user.is_authenticated:
        return redirect(reverse('dashboard'))

    register_form = f.RegisterForm()
    shipping_form = f.ShippingForm()
    context = {'register_form': register_form, 'shipping_form': shipping_form}
    if request.POST:
        register_form = f.RegisterForm(request.POST)
        shipping_form = f.ShippingForm(request.POST)
        if register_form.is_valid() and shipping_form.is_valid():
            new_user = register_form.save()
            new_address = m.ShippingAddress(
                customer=new_user,
                street_1=shipping_form['street_1'].data,
                street_2=shipping_form['street_2'].data,
                zip=shipping_form['zip'].data
            )
            new_address.save()

            login(request, new_user)
            messages.success(request, 'Thank you for registering! This is your dashboard.')
            return redirect(reverse('dashboard'))
        else:
            messages.warning(request, 'There was an error in your application, please review it.')

    return render(request, "registration/sign_up.html", context=context)


def login_user(request):
    if request.user.is_authenticated:
        return redirect(reverse('dashboard'))
    else:
        if request.POST:
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)

                return redirect(reverse('dashboard'))
        else:
            form = AuthenticationForm(request)
            context = {'form': form}
            return render(request, "registration/login.html", context=context)


def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect(reverse('login'))


def dashboard(request):
    context = {}
    if request.user.is_authenticated:
        customer = request.user
        orders = m.Order.objects.filter(customer=customer, complete=True)
        context['orders'] = orders
        if request.POST:
            shipping_form = f.ShippingForm(request.POST)
            if shipping_form.is_valid():
                new_address = m.ShippingAddress(
                    customer=request.user,
                    street_1=shipping_form['street_1'].data,
                    street_2=shipping_form['street_2'].data,
                    zip=shipping_form['zip'].data
                )
                new_address.save()
            return redirect(reverse('dashboard'))

        else:
            try:
                address = m.ShippingAddress.objects.filter(customer=request.user.id)
                if len(address) > 1:
                    shipping_form = f.ShippingForm()
                    context['shipping_form'] = shipping_form
                    context['multiple_address'] = address
                    return render(request, "main/dashboard.html", context=context)
                if len(address) == 1:
                    data = {'street_1': address[0].street_1,
                            'street_2': address[0].street_2,
                            'zip': address[0].zip}
                    shipping_form = f.ShippingForm(data)
                    context['shipping_form'] = shipping_form
                    context['single_address'] = address[0]
                    return render(request, "main/dashboard.html", context=context)
                else:
                    shipping_form = f.ShippingForm()
                    context['no_address'] = True
                    context['shipping_form'] = shipping_form
                    return render(request, "main/dashboard.html", context=context)
            except Exception as e:
                print(e)

            return render(request, "main/dashboard.html", context=context)
    else:
        return redirect(reverse('home'))


def delete_address(request):
    if request.user.is_authenticated:
        data = json.loads(request.body)
        address_id = data['address_id']
        to_delete = m.ShippingAddress.objects.get(id=address_id)
        to_delete.delete()
        return JsonResponse('item added to the cart', safe=False)

    else:
        return redirect(reverse('home'))


def details(request, slug):
    context = {}
    slug = slug
    try:
        selected = m.Product.objects.get(slug=slug)
        print(slug)
        context = {'selected': selected}
    except Exception as e:
        print('exception on details page', e)
    return render(request, "main/details.html", context=context)


def added_to_cart(request):
    if request.user.is_authenticated:
        if request.POST:
            quantity = request.POST['quantity']
            product_id = request.POST['product_id']
            customer = request.user
            product = m.Product.objects.get(id=product_id)
            order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
            orderItem, created = m.OrderItem.objects.get_or_create(order=order, product=product)
            orderItem.quantity += int(quantity)
            orderItem.save()
            return redirect(reverse('cart'))
    else:
        product_id = int(request.POST['product_id'])
        quantity = request.POST['quantity']

        if 'shopping_data' not in request.session:
            request.session['shopping_data'] = []
        try:
            cart_list = request.session["shopping_data"]
            for i in cart_list:
                if i["product"] == int(product_id):
                    i['quantity'] += int(quantity)
                    request.session["shopping_data"] = cart_list
                    print(request.session['shopping_data'])
                    return redirect(reverse('cart'))
        except Exception as e:
            print(e)

        new_add = {
            'product': int(product_id),
            'quantity': int(quantity)
        }
        cart_list = request.session["shopping_data"]
        cart_list.append(new_add)
        request.session["shopping_data"] = cart_list

        return redirect(reverse('cart'))


def cart(request):
    # if the user is auth, then we get the customer linked to them
    context = {}
    if request.user.is_authenticated:
        customer = request.user
        # here we create or get the order, and find one that matches the customer in turn and is also open
        order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
        # then get the items of this particular order and send them to the context dict
        items = order.orderitem_set.all()
        if len(items) == 0:
            context['empty_cart'] = True
            return render(request, "main/cart.html", context=context)

        context['items'] = items
        # finally we gather the whole order, in order to use the get methods for total prices and quantities
        context['order'] = order
    else:
        products_in_cart = []
        try:
            for i in request.session['shopping_data']:
                add = {
                    'product': m.Product.objects.get(id=i['product']),
                    'quantity': i['quantity'],
                }
                add['stripe_price_id'] = add['product'].stripe_price_id
                add['price'] = add['product'].price * add['quantity']
                products_in_cart.append(add)
            context['guest_user_items'] = products_in_cart
            print(products_in_cart)

            total_items = sum(i['quantity'] for i in products_in_cart)
            context['total_items'] = total_items

            total_to_pay = sum((i['product'].price * i['quantity']) for i in products_in_cart)
            context['total_to_pay'] = total_to_pay

            if len(products_in_cart) == 0:
                context = {'empty_cart': True}

        except Exception as e:
            print(e)
            context = {'empty_cart': True}
        print(products_in_cart)
    return render(request, "main/cart.html", context=context)


def checkout(request):
    context = {}
    if request.user.is_authenticated:
        if request.POST:
            shipping_form = f.ShippingForm(request.POST)
            if shipping_form.is_valid():
                new_address = m.ShippingAddress(
                    customer=request.user,
                    street_1=shipping_form['street_1'].data,
                    street_2=shipping_form['street_2'].data,
                    zip=shipping_form['zip'].data
                )
                new_address.save()
                return redirect(reverse('checkout'))

        customer = request.user
        # here we create or get the order, and find one that matches the customer in turn and is also open
        order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
        request.session['order_id'] = order.id
        print('order id: ', request.session['order'])
        # then get the items of this particular order and send them to the context dict
        items = order.orderitem_set.all()
        context['items'] = items
        if not items:
            return render(request, "main/checkout.html", context=context)
        else:
            # finally we gather the whole order, in order to use the get methods for total prices and quantities
            context['order'] = order
            context['user'] = request.user
            try:
                address = m.ShippingAddress.objects.filter(customer=request.user.id)
                if len(address) > 1:
                    context['multiple_address'] = address
                    return render(request, "main/checkout.html", context=context)
                if len(address) == 1:
                    data = {'street_1': address[0].street_1,
                            'street_2': address[0].street_2,
                            'zip': address[0].zip}
                    shipping_form = f.ShippingForm(data)
                    context['shipping_form'] = shipping_form
                    context['single_address'] = address[0]
                    return render(request, "main/checkout.html", context=context)
                else:
                    shipping_form = f.ShippingForm()
                    context['no_address'] = True
                    context['shipping_form'] = shipping_form
                    return render(request, "main/checkout.html", context=context)
            except Exception as e:
                print(e)

    else:
        user_form = f.GuestUserSaveForm()
        context['guest_user_form'] = user_form

        guest_shipping_form = f.GuestUserShippingForm()
        context['guest_shipping_form'] = guest_shipping_form

        products_in_cart = []
        try:
            for i in request.session['shopping_data']:
                add = {
                    'product': m.Product.objects.get(id=i['product']),
                    'quantity': i['quantity'],
                }
                add['stripe_price_id'] = add['product'].stripe_price_id
                add['price'] = add['product'].price * add['quantity']
                products_in_cart.append(add)
            context['guest_user_items'] = products_in_cart

            total_items = sum(i['quantity'] for i in products_in_cart)
            context['total_items'] = total_items

            total_to_pay = sum((i['product'].price * i['quantity']) for i in products_in_cart)
            context['total_to_pay'] = total_to_pay

            if len(products_in_cart) == 0:
                context = {'empty_cart': True}
        except Exception as e:
            print(e)
        return render(request, "main/checkout.html", context=context)
    return render(request, "main/checkout.html", context=context)


def guest_checkout(request):
    context = {}
    if request.POST:
        guest_form = f.GuestUserSaveForm(request.POST)
        if guest_form.is_valid():
            address_form = f.GuestUserShippingForm(request.POST)
            if address_form.is_valid():
                new_guest_user = m.GuestUser(
                    f_name=guest_form['f_name'].data,
                    l_name=guest_form['l_name'].data,
                    phone=guest_form['phone'].data,
                    email=guest_form['email'].data,

                )
                new_guest_user.save()

                new_address = m.GuestUserAddress(
                    customer=new_guest_user,
                    street_1=address_form['street_1'].data,
                    street_2=address_form['street_2'].data,
                    zip=address_form['zip'].data,
                )
                new_address.save()

                transaction_id = datetime.datetime.now().timestamp()
                new_guest_order = m.GuestUserOrder(customer=new_guest_user,
                                                   address=new_address,
                                                   order_id=transaction_id,
                                                   complete=True)
                new_guest_order.save()

                products_in_cart = []
                try:
                    for i in request.session['shopping_data']:
                        add = {
                            'product': m.Product.objects.get(id=i['product']),
                            'quantity': i['quantity'],
                        }
                        add['price'] = add['product'].price * add['quantity']
                        products_in_cart.append(add)
                except Exception as e:
                    print('Exception from guest_checkout, line 390: ', e)
                try:
                    for i in products_in_cart:
                        new_item = m.GuestUserOrderItem(product=i['product'],
                                                        order=new_guest_order,
                                                        quantity=i['quantity'])
                        new_item.save()

                except Exception as e:
                    print(e)
                context = {'order': new_guest_order}
                request.session['shopping_data'] = []
        return render(request, "main/order_complete.html", context=context)


def set_address(request):
    context = {}
    if request.user.is_authenticated:
        if request.POST:
            print('the post request from the form is valid, bitch!')
            data = {'street_1': request.POST['street_1'],
                    'street_2': request.POST['street_2'],
                    'zip': request.POST['zip']}
            shipping_form = f.ShippingForm(data)
            context['shipping_form'] = shipping_form
            context['single_address'] = True

            customer = request.user
            # here we create or get the order, and find one that matches the customer in turn and is also open
            order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
            # then get the items of this particular order and send them to the context dict
            items = order.orderitem_set.all()
            context['items'] = items
            context['order'] = order
            if not items:
                return render(request, "main/checkout.html", context=context)
            return render(request, "main/checkout.html", context=context)
        else:
            return redirect(reverse('home'))
    else:
        return redirect(reverse('home'))


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
    if request.user.is_authenticated:
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

        if 'shopping_data' not in request.session:
            request.session['shopping_data'] = []
        try:
            print('try')
            cart_list = request.session["shopping_data"]
            for i in cart_list:
                if i["product"] == product_id:
                    print('catch the ID')
                    if action == 'add':
                        i['quantity'] += 1

                    elif action == 'remove':
                        i['quantity'] -= 1

                    if action == 'delete' or i['quantity'] <= 0:
                        cart_list.remove(i)

                    request.session["shopping_data"] = cart_list
                    print('update item. uth user', request.session['shopping_data'])
                    return JsonResponse('item added to the cart', safe=False)
        except Exception as e:
            print(e)

        new_add = {
            'product': product_id,
            'quantity': 0
        }

        if action == 'add':
            new_add['quantity'] += 1

        cart_list = request.session["shopping_data"]
        cart_list.append(new_add)
        request.session["shopping_data"] = cart_list

    else:
        if 'shopping_data' not in request.session:
            request.session['shopping_data'] = []
        try:
            print('try')
            cart_list = request.session["shopping_data"]
            for i in cart_list:
                if i["product"] == product_id:
                    print('catch the ID')
                    if action == 'add':
                        i['quantity'] += 1

                    elif action == 'remove':
                        i['quantity'] -= 1

                    if action == 'delete' or i['quantity'] <= 0:
                        cart_list.remove(i)

                    request.session["shopping_data"] = cart_list
                    print(request.session['shopping_data'])
                    return JsonResponse('item added to the cart', safe=False)
        except Exception as e:
            print(e)

        new_add = {
            'product': product_id,
            'quantity': 0
        }

        if action == 'add':
            new_add['quantity'] += 1

        cart_list = request.session["shopping_data"]
        cart_list.append(new_add)
        request.session["shopping_data"] = cart_list

        print(request.session['shopping_data'])
        return JsonResponse('item added to the cart', safe=False)

    return JsonResponse('item added to the cart', safe=False)


def process_order(request):
    data = json.loads(request.body)
    transaction_id = datetime.datetime.now().timestamp()
    customer = request.user
    order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
    order.order_id = transaction_id
    total_to_pay = float(data['total'])
    order_total = float(order.get_total_price)

    if total_to_pay == order_total:
        order.complete = True
        order.save()

    return JsonResponse('Order Completed', safe=False)


def order_complete(request):
    context = {}
    return render(request, 'main/order_complete.html', context=context)


@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_key_config = {'public_key': settings.STRIPE_KEYS['public_key']}
        return JsonResponse(stripe_key_config, safe=False)


@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        domain_url = 'http://127.0.0.1:8000/'
        stripe.api_key = settings.STRIPE_KEYS['secret_key']

        products_in_cart = []
        for i in request.session['shopping_data']:
            add = {
                'product': m.Product.objects.get(id=i['product']),
                'quantity': i['quantity'],
            }
            add['stripe_price_id'] = add['product'].stripe_price_id
            add['price'] = add['product'].price * add['quantity']
            products_in_cart.append(add)

        line_items = []
        for i in products_in_cart:
            item = {
                'quantity': i['quantity'],
                'price': i['stripe_price_id'],
            }
            line_items.append(item)
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=request.session['order_id'],
                success_url=domain_url + 'order_complete/',
                cancel_url=domain_url + 'checkout',
                payment_method_types=['card'],
                mode='payment',
                line_items=line_items,
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_KEYS['secret_key']
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body

    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']["client_reference_id"]
        print('payload:', session)

        transaction_id = datetime.datetime.now().timestamp()
        order = m.Order.objects.get(id=session)
        order.order_id = transaction_id
        order.complete = True
        order.save()
        print("Payment was successful!!!.")

        """transaction_id = datetime.datetime.now().timestamp()
        customer = request.user
        print('customer id for final checkout: ', customer)
        order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
        order.order_id = transaction_id
        order.complete = True
        order.save()
        print("order completed!!!")"""

    return HttpResponse(status=200)

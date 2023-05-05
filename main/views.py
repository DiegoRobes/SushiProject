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
# stripe imports
import stripe
from django.conf import settings
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# to render the home view, we first query the products from the DB using their corresponding tags and send them to
# the page to be rendered via the context dictionary
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


# the about us page, no operation needs to be performed here. just a simple render
def about(request):
    context = {}
    return render(request, "main/about.html", context=context)


# here first we check if the user is authenticated already, if so, we send them to the user dashboard (see bellow)
# if user is still anonymous, present them with both options for sign up or login
def welcome(request):
    context = {}
    if request.user.is_authenticated:
        return redirect(reverse('dashboard'))
    else:
        return render(request, "main/welcome.html", context=context)


# first check if user is authenticated, if so, send them to dashboard
# in GET method, create an instance of both RegisterForm and ShippingForm (imported above), and send them to the
# template via context
def sign_up(request):
    context = {}
    if request.user.is_authenticated:
        return redirect(reverse('dashboard'))

    register_form = f.RegisterForm()
    shipping_form = f.ShippingForm()
    context['register_form'] = register_form
    context['shipping_form'] = shipping_form

    # in POST method, gather the info from the forms and validate the forms. Register form can be easily saved into the
    # database because it uses the UserCreationForm class (check forms.py). For the address, we manually get the info
    # and create a new object to be placed into the database. Finally, login the newly created user and send them to
    # their user dashboard with a success message.
    # if either form is not valid, send a warning message and repeat the process.
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


# first check if user is authenticated, if so, send them to dashboard
# to log in the user we will use the ready-made AuthenticationForm, this way the process will be done using the powers
# of Django. in GET method we create the form and send it via context to the render. in POST, we use the get_user()
# method from the AuthenticationForm to check if email and password are correct, and if so, login the user via the
# built-in login() function that comes with django (imported above). finally, we redirect the user to their dashboard
# once logged in
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


# use the built-in logout() function, feeding it the request, to log out the user. also, when this happens,
# request.session['shopping_data'] get emptied to ensure the next user has a brand-new shopping cart
def logout_user(request):
    if request.user.is_authenticated:
        request.session['shopping_data'] = []
        logout(request)
        return redirect(reverse('login'))


# first check if user is authenticated, if not, send them to 'welcome' page to log in or sing up
def dashboard(request):
    context = {}
    # if user is authenticated, first get all orders matching this user from the db and send the query to the context
    # dict, so we can extract the info on these orders to be rendered
    if request.user.is_authenticated:
        customer = request.user
        orders = m.Order.objects.filter(customer=customer, complete=True)
        context['orders'] = orders

        # the POST method on this view is used to handle the addition of new addresses to the DB, note how every address
        # is linked to the corresponding user
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

        # the GET method is used to try to make a query with the addresses linked to this particular user. 3 previsions
        # are made: 1- they have more than one address, 2- they have only one address, 3- they don't have any addresses
        # yet. these previsions are important because they change the way the page will be rendered. check how in every
        # case we pass the shipping_form form to the context so the user can create a new address, but also the context
        # can change depending on the number of addresses we can link to the user. this adaptable context will determine
        # the way the page is rendered
        else:
            try:
                address = m.ShippingAddress.objects.filter(customer=request.user.id)
                # multiple addresses
                if len(address) > 1:
                    shipping_form = f.ShippingForm()
                    context['shipping_form'] = shipping_form
                    context['multiple_address'] = address
                    return render(request, "main/dashboard.html", context=context)
                # single address
                if len(address) == 1:
                    data = {'street_1': address[0].street_1,
                            'street_2': address[0].street_2,
                            'zip': address[0].zip}
                    shipping_form = f.ShippingForm(data)
                    context['shipping_form'] = shipping_form
                    context['single_address'] = address[0]
                    return render(request, "main/dashboard.html", context=context)
                # no address
                else:
                    shipping_form = f.ShippingForm()
                    context['no_address'] = True
                    context['shipping_form'] = shipping_form
                    return render(request, "main/dashboard.html", context=context)
            except Exception as e:
                print(e)

            return render(request, "main/dashboard.html", context=context)
    else:
        return redirect(reverse('welcome'))


# this function handles an XML request made by a javascript function inside the dashboard.html file. the function asks
# the server to delete from the database an address that the user has requested. We unpack the body of the request to
# get the ID of the address we need to delete, find it in the DB and simply use the delete() function. This XML function
# is better understood from the html file
def delete_address(request):
    if request.user.is_authenticated:
        data = json.loads(request.body)
        address_id = data['address_id']
        to_delete = m.ShippingAddress.objects.get(id=address_id)
        to_delete.delete()
        return JsonResponse('Address has been deleted', safe=False)
    else:
        return redirect(reverse('home'))


# This function takes an argument that is generated by each thumbnail in the index view, and uses it to feed the slug
# this slug is then used to find the Product object with a matching slug. we send this object to the view via the
# context dictionary to be rendered
def details(request, slug):
    context = {}
    slug = slug
    try:
        selected = m.Product.objects.get(slug=slug)
        context = {
            'selected': selected
        }
    except Exception as e:
        print('exception on details page:', e)
    return render(request, "main/details.html", context=context)


# this function is divided in 2 parts, first we deal with authenticated users:
# in the 'details' view, a hidden form is rendered. this forms sends to the server the id of the product being viewed,
# so a quick get() can be performed, and we find the Product Object. then we take the quantity of the product the user
# asked for and use it to modify any opened orders from this particular user. note that the order is being modified via
# a get_or_create() function on the item, meaning that we are going to either add the product to the order, or just
# modify its quantity. this helps us avoid duplicates. finally, send the user to check their shopping carts
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
    # this part of the function is different because here we cannot get an Order Object, nor OrderItem objects from the
    # database, this is because the user is not authenticated yet. no user = no order = no orderItem.
    # if this anon user has already opened an order via the request.session["shopping_data"], we try to modify the
    # quantity of this particular product if it is already in the dict, if not, we add it as a new add. finally redirect
    # the user to the same shopping cart view
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
    context = {}
    if request.user.is_authenticated:
        customer = request.user
        order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()

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

        except Exception as e:
            print(e)

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
        else:
            # get customer, matching opened order, items in the order, and send the order id to the session,
            # as well as  order and items to the context
            customer = request.user
            order, created = m.Order.objects.get_or_create(customer=customer, complete=False)
            request.session['order_id'] = order.id
            print('order ID for auth user sent to session', request.session['order_id'])

            items = order.orderitem_set.all()

            context['items'] = items
            context['order'] = order

            # restart the 'shopping_data' everytime this page is requested, this is the easiest way to  avoid
            # duplicates in the session everytime the items query is updated.
            # Then iterate through the items query and use their properties to feed each dictionary in 'shopping_data'
            products_in_cart = []
            request.session['shopping_data'] = []

            try:
                for i in items:
                    add_to_SD = {
                        'product': int(i.product.id),
                        'quantity': i.quantity
                    }

                    request.session['shopping_data'].append(add_to_SD)
            except Exception as e:
                print(e)

            if not items:
                return render(request, "main/checkout.html", context=context)

            # finally check if the cx has no, one or many addresses and use the context dict properly
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

            # this is the main render of the GET method
            return render(request, "main/checkout.html", context=context)
    # if user in not authenticated, we have a function specially made for them. this is to avoid making this one too
    # convoluted
    else:
        return redirect(reverse('guest_checkout'))


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
                data = {'f_name': new_guest_user.f_name,
                        'l_name': new_guest_user.l_name,
                        'phone': new_guest_user.phone,
                        'email': new_guest_user.email
                        }
                user_form = f.GuestUserSaveForm(data)
                context['guest_user_form'] = user_form

                new_address = m.GuestUserAddress(
                    customer=new_guest_user,
                    street_1=address_form['street_1'].data,
                    street_2=address_form['street_2'].data,
                    zip=address_form['zip'].data,
                )
                new_address.save()
                data = {'street_1': new_address.street_1,
                        'street_2': new_address.street_2,
                        'zip': new_address.zip}
                address_form = f.GuestUserShippingForm(data)
                context['guest_shipping_form'] = address_form

                new_guest_order = m.GuestUserOrder(customer=new_guest_user,
                                                   address=new_address,
                                                   complete=False)
                new_guest_order.save()
                request.session['order_id'] = 'GU_' + str(new_guest_order.id)
                print(request.session['order_id'])

                products_in_cart = []
                print('this is the cart from POST guest', request.session['shopping_data'])
                try:
                    for i in request.session['shopping_data']:
                        add = {
                            'product': m.Product.objects.get(id=i['product']),
                            'quantity': i['quantity'],
                        }
                        add['price'] = add['product'].price * add['quantity']
                        add['stripe_price_id'] = add['product'].stripe_price_id
                        products_in_cart.append(add)
                        context['guest_user_items'] = products_in_cart
                        print('this is the p in cart list from guest POST', products_in_cart)

                        total_items = sum(i['quantity'] for i in products_in_cart)
                        context['total_items'] = total_items

                        total_to_pay = sum((i['product'].price * i['quantity']) for i in products_in_cart)
                        context['total_to_pay'] = total_to_pay

                except Exception as e:
                    print('Exception from guest_checkout, line 410: ', e)
                try:
                    for i in products_in_cart:
                        new_item = m.GuestUserOrderItem(product=i['product'],
                                                        order=new_guest_order,
                                                        quantity=i['quantity'])
                        new_item.save()
                except Exception as e:
                    print(e)
                context['order'] = new_guest_order
        return render(request, "main/guest_checkout.html", context=context)

    else:
        context = {}
        user_form = f.GuestUserSaveForm()
        context['guest_user_form'] = user_form

        guest_shipping_form = f.GuestUserShippingForm()
        context['guest_shipping_form'] = guest_shipping_form

        products_in_cart = []
        print('this is the cart from the guest user check', request.session['shopping_data'])
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

            print('this is the p in cart list from guest user', products_in_cart)

            total_items = sum(i['quantity'] for i in products_in_cart)
            context['total_items'] = total_items

            total_to_pay = sum((i['product'].price * i['quantity']) for i in products_in_cart)
            context['total_to_pay'] = total_to_pay
            if len(products_in_cart) == 0:
                context = {'empty_cart': True}
        except Exception as e:
            print(e)
        return render(request, "main/guest_checkout.html", context=context)


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
            print(request.session['shopping_data'])
            print('try from auth userrrrr')
            cart_list = request.session["shopping_data"]
            print('cart list:', cart_list)
            for i in cart_list:
                if i["product"] == product_id:
                    print('catch the ID')
                    if action == 'add':
                        i['quantity'] += 1

                    elif action == 'remove':
                        i['quantity'] -= 1

                    elif action == 'delete' or i['quantity'] == 0:
                        cart_list.remove(i)

                    request.session["shopping_data"] = cart_list
                    print('update item from auth user', request.session['shopping_data'])
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
    request.session['shopping_data'] = []
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

        print('shopping data from ccs:', request.session['shopping_data'])
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

        if session.startswith('GU_'):
            replacements = [('G', ''), ('U', ''), ('_', '')]
            for char, replacement in replacements:
                if char in session:
                    session = session.replace(char, replacement)
            transaction_id = datetime.datetime.now().timestamp()
            order = m.GuestUserOrder.objects.get(id=session)
            order.order_id = transaction_id
            order.complete = True
            order.save()
            print('payload:', session)
        else:
            transaction_id = datetime.datetime.now().timestamp()
            order = m.Order.objects.get(id=session)
            order.order_id = transaction_id
            order.complete = True
            order.save()

    return HttpResponse(status=200)

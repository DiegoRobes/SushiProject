from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# user is OneToOne bc one customer can only have one username
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    f_name = models.CharField(max_length=200, null=True)
    l_name = models.CharField(max_length=200, null=True)
    email = models.EmailField(max_length=200)

    def __str__(self):
        return str(self.f_name) + str(self.l_name)


class Tag(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=100, default="")
    slug = models.SlugField(max_length=200, unique=True)

    # this one creates a slug for any new entry on the tag models
    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
        return super(Tag, self).save(self, *args, **kwargs)

    def __str__(self):
        return self.name


# simple product model. the slug is important to pass as an url argument latter
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.FloatField()
    img = models.ImageField(null=False, blank=True, upload_to='products/', default=None)
    tag = models.ManyToManyField(Tag, blank=True, related_name='product')
    slug = models.SlugField(max_length=50, unique=True, default=None)
    featured = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# we use the customer as the foreign key to map every order to a user/customer
# on_delete is set this way to make sure the order is not deleted from the db if the user decides to
# destroy their account. blank and null are so an unregistered user (guest) can make an order.
# complete is a boolean that is set to false, this is to be able to add articles to the order as long as the order is
# still in progress. we don't commit the object to the db until this bool is True
# YOUR ORDER IS YOUR CART
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    complete = models.BooleanField(default=False, null=True, blank=True)
    order_id = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


# ORDER ITEM IS A PRODUCT INSIDE THE CART
# keep in mind that we will have many OI, and all of them will be mapped to a product, to know which product it is,
# and to an order, to know which order it belongs to. quantity to know how many of this particular product,
# and finally date
class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)


# the shipping model has a field mapped to the customer, to know who this address object belongs to, and to an order,
# to link it to a particular cart and all of its contents
class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True)
    street_1 = models.CharField(max_length=100, null=False, unique=False)
    street_2 = models.CharField(max_length=100, null=False, unique=False)
    zip = models.CharField(max_length=100, null=False, unique=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.street_1) + str(self.street_2)


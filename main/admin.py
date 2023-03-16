from django.contrib import admin
from . import models as m

# Register your models here.
admin.site.register(m.Customer)
admin.site.register(m.Product)
admin.site.register(m.Order)
admin.site.register(m.OrderItem)
admin.site.register(m.ShippingAddress)
admin.site.register(m.Tag)

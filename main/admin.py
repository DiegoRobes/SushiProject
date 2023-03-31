from django.contrib import admin
from . import models as m

# Models for users
admin.site.register(m.Product)
admin.site.register(m.Order)
admin.site.register(m.OrderItem)
admin.site.register(m.ShippingAddress)
admin.site.register(m.Tag)

# Models for guests
admin.site.register(m.GuestUser)
admin.site.register(m.GuestUserAddress)
admin.site.register(m.GuestUserOrder)
admin.site.register(m.GuestUserOrderItem)

# visitors/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Payment  # your custom user model

# Register User model
admin.site.register(User, UserAdmin)

# Register Payment model with error handling to avoid re-registration
from django.contrib import admin

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'payment_date')  # Customize fields as needed

try:
    admin.site.register(Payment, PaymentAdmin)
except admin.sites.AlreadyRegistered:
    pass
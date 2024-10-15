from django.db import models
from django.contrib.auth.models import User

class UserPayment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_customer = models.CharField(max_length=500, blank=True)
    stripe_checkout_id = models.CharField(max_length=500, blank=True)
    stripe_product_id = models.CharField(max_length=500, blank=True)
    product_name = models.CharField(max_length=500, blank=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    currency = models.CharField(max_length=3, blank=True)
    has_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.product_name} - Paid: {self.has_paid}"

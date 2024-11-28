from django.db import models
from django.contrib.auth.models import User
from colorfield.fields import ColorField 

import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY


class ProductColor(models.Model):
    name = models.CharField(max_length=100)
    color = ColorField(default='#000000') 
    
    def __str__(self):
        return self.name
    
    
class ProductSize(models.Model):
    name = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
    
class ProductVariation(models.Model):
    product_id = models.CharField(max_length=255)
    colors = models.ManyToManyField(ProductColor)
    sizes = models.ManyToManyField(ProductSize)
    
    @property
    def prices(self):
        prices = []
        price_list = stripe.Price.list(product=self.product_id)
        for price in price_list['data']:
            quality = price['metadata'].get('quality') or 'Normal'
            prices.append({
                'quality': quality,
                'price': price['unit_amount'] / 100,
            })
        prices = sorted(prices, key=lambda x: x['price'])
        return prices
    
    def get_price(self, quality=None):
        if quality:
            price_list = stripe.Price.list(product=self.product_id)
            for price in price_list['data']:
                price_quality = price['metadata'].get('quality') or None
                if price_quality and price_quality.lower() == quality.lower():
                    return price
        product = stripe.Product.retrieve(self.product_id)
        default_price_id = product.default_price
        price = stripe.Price.retrieve(default_price_id)
        return price
    
    def __str__(self):
        product = stripe.Product.retrieve(self.product_id)
        return product['name']
    
    
class ProductVariationObject(models.Model):
    product = models.ForeignKey(ProductVariation, on_delete=models.CASCADE)
    color = models.ForeignKey(ProductColor, on_delete=models.SET_NULL, null=True)
    image_front = models.ImageField(upload_to="product_variations/", blank=True, null=True)
    image_back = models.ImageField(upload_to="product_variations/", blank=True, null=True)
    featured = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if self.featured:
            ProductVariationObject.objects.filter(product=self.product).update(featured=False)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.product} - {self.color}"
    
    
class ShippingInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address_line_one = models.CharField(max_length=255)
    address_line_two = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    
class CheckoutSession(models.Model):
    checkout_id = models.CharField(max_length=255)
    shipping_info = models.ForeignKey(ShippingInfo, on_delete=models.SET_NULL, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    has_paid = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created']
        
    def __str__(self):
        date = self.created.strftime('%d/%m/%Y') 
        return f'{self.checkout_id} - {self.shipping_info} - ${self.total_cost} - {date} - Paid: {self.has_paid}'

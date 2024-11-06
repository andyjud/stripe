from django.shortcuts import render, redirect, reverse
import stripe
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import *
from .utils import *
from .cart import Cart

stripe.api_key = settings.STRIPE_SECRET_KEY

def shop_view(request):
    products_list = stripe.Product.list()
    products = []
    
    for product in products_list['data']:
        if product.get('metadata', {}).get('category') == "shop":
            products.append(get_product_details(product)) 
        
    return render(request, 'a_stripe/shop.html', {'products': products})


def product_view(request, product_id):
    product = stripe.Product.retrieve(product_id)
    product_details = get_product_details(product)
    
    cart = Cart(request)
    product_details['in_cart'] = product_id in cart.cart_session
    
    return render(request, 'a_stripe/product.html', {'product': product_details})


def add_to_cart(request, product_id):
    cart = Cart(request)
    cart.add(product_id)
    
    product = stripe.Product.retrieve(product_id)
    product_details = get_product_details(product)
    product_details['in_cart'] = product_id in cart.cart_session

    response = render(request, 'a_stripe/partials/cart-button.html', {'product': product_details})
    response['HX-Trigger'] = 'hx_menu_cart'
    return response


def hx_menu_cart(request):
    return render(request, 'a_stripe/partials/menu-cart.html' )


def cart_view(request):
    quantity_range = list(range(1, 11)) 
    return render(request, 'a_stripe/cart.html', {'quantity_range': quantity_range})


def update_checkout(request, product_id):
    quantity = int(request.POST.get('quantity', 1))
    cart = Cart(request)
    cart.add(product_id, quantity)
    
    product = stripe.Product.retrieve(product_id)
    product_details = get_product_details(product)
    product_details['total_price'] = product_details['price'] * quantity

    response = render(request, 'a_stripe/partials/checkout-total.html', {'product' : product_details}) 
    response['HX-Trigger'] = 'hx_menu_cart'
    return response


def remove_from_cart(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    return redirect('cart')

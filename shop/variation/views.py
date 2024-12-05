from django.shortcuts import render, redirect, reverse
import stripe
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import *
from .utils import *
from .cart import Cart
from .forms import *

stripe.api_key = settings.STRIPE_SECRET_KEY

def shop_view(request):
    # del request.session[settings.CART_SESSION_ID]
    products_list = stripe.Product.list()
    products = []
    
    for product in products_list['data']:
        if product.get('metadata', {}).get('category') == "shop":
            products.append(get_product_details(product, None)) 
        
    return render(request, 'a_stripe/shop.html', {'products': products})


def product_view(request, product_id):
    product_variation = ProductVariation.objects.filter(product_id=product_id).first()
    quality = None 
    if product_variation:
        product_variation_list = ProductVariationObject.objects.filter(product=product_variation)
        product_variation_obj = product_variation_list.filter(featured=True).first() or product_variation_list.first()
    
        color = request.GET.get('color') or None
        if color:
            color_obj = ProductColor.objects.get(name__iexact=color)
            product_variation_obj = product_variation_list.get(color=color_obj)
            
        size = request.GET.get('size') or 's'
        quality = request.GET.get('quality') or 'normal'
    
    product = stripe.Product.retrieve(product_id)
    product_details = get_product_details(product, quality)

    context = {
       'product': product_details,
    }
    
    if product_variation:
        context.update({
            'product_variation': product_variation,
            'product_variation_obj': product_variation_obj,
            'color': color,
            'size': size,
            'quality': quality,
        })
    
    return render(request, 'a_stripe/product.html', context)


def add_to_cart(request, product_id):
    product = stripe.Product.retrieve(product_id)
    product_variation = ProductVariation.objects.filter(product_id=product_id).first()
    try:
        featured_product = ProductVariationObject.objects.get(product=product_variation, featured=True)
        featured_product_color = featured_product.color.name
    except:
        featured_product_color = None
    color = request.GET.get('color') or featured_product_color 
    color = color.capitalize() if color else None
    
    size = request.GET.get('size') or ('s' if product_variation else None)
    size = size.upper() if size else None
    
    quality = request.GET.get('quality') or ('normal' if product_variation else None)
    quality = quality.capitalize() if quality else None
    
    try:
        color_obj = ProductColor.objects.get(name__iexact=color)
        product_variation_obj = ProductVariationObject.objects.get(product=product_variation, color=color_obj)
        image = request.build_absolute_uri(product_variation_obj.image_front.url)
    except:
        image = product['images'][0]
    
    cart = Cart(request)
    cart.add(product_id, color=color, size=size, quality=quality, image=image)
    
    product_details = get_product_details(product, quality)
    product_details['in_cart'] = product_id in cart.cart_session

    response = render(request, 'a_stripe/partials/cart-button.html', {'product': product_details})
    response['HX-Trigger'] = 'hx_menu_cart'
    return response


def hx_menu_cart(request):
    return render(request, 'a_stripe/partials/menu-cart.html' )


def cart_view(request):
    quantity_range = list(range(1, 11)) 
    return render(request, 'a_stripe/cart.html', {'quantity_range': quantity_range})


def update_checkout(request, item_id):
    quantity = int(request.POST.get('quantity', 1))
    quality = request.POST.get('quality')
    cart = Cart(request)
    product_id = cart.cart_session.get(item_id)['product_id']
    cart.add(product_id, quantity, item_id=item_id)
    
    product = stripe.Product.retrieve(product_id)
    product_details = get_product_details(product, quality)
    product_details['total_price'] = product_details['price'] * quantity
    product_details['item_id'] = item_id

    response = render(request, 'a_stripe/partials/checkout-total.html', {'product' : product_details}) 
    response['HX-Trigger'] = 'hx_menu_cart'
    return response


def remove_from_cart(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    return redirect('cart')


@login_required
def checkout_view(request):
    shipping_info = ShippingInfo.objects.filter(user=request.user).first()
    
    if shipping_info:
        form = ShippingForm(instance=shipping_info)
    else:
        form = ShippingForm(initial={'email': request.user.email})
    
    if request.method == 'POST':
        form = ShippingForm(request.POST, instance=shipping_info)
        if form.is_valid():
            shipping_info = form.save(commit=False)
            shipping_info.user = request.user
            shipping_info.email = form.cleaned_data['email'].lower()
            shipping_info.save()
            
            cart = Cart(request)
            checkout_session = create_checkout_session(cart, shipping_info.email)
            
            CheckoutSession.objects.create(
                checkout_id = checkout_session.id,
                shipping_info = shipping_info,
                total_cost = cart.get_total_cost()
            )
            
            return redirect(checkout_session.url, code=303)
    
    return render(request, 'a_stripe/checkout.html', {'form': form})



def payment_successful(request):
    checkout_session_id = request.GET.get('session_id', None)
    
    if checkout_session_id:
        session = stripe.checkout.Session.retrieve(checkout_session_id)
        customer_id = session.customer
        customer = stripe.Customer.retrieve(customer_id)
        
        if settings.CART_SESSION_ID in request.session:
            del request.session[settings.CART_SESSION_ID]
            
        if settings.DEBUG:
            checkout = CheckoutSession.objects.get(checkout_id=checkout_session_id)
            checkout.has_paid = True
            checkout.save()
    
    return render(request, 'a_stripe/payment_successful.html', {'customer': customer})


def payment_cancelled(request):
    return render(request, 'a_stripe/payment_cancelled.html')


@require_POST
@csrf_exempt
def stripe_webhook(request):
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    signature_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    
    try:
        event = stripe.Webhook.construct_event(
            payload, signature_header, endpoint_secret
        )
    except:
        return HttpResponse(status=400)
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        checkout_session_id = session.get('id')
        checkout = CheckoutSession.objects.get(checkout_id=checkout_session_id)
        checkout.has_paid = True
        checkout.save()
        
    return HttpResponse(status=200)

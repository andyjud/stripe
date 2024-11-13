import stripe
from django.conf import settings
from django.urls import reverse

def get_product_details(product):
    prices = stripe.Price.list(product=product['id'])
    price = prices['data'][0]
    product_details ={
        'id': product['id'],
        'name': product['name'],
        'image': product['images'][0],
        'description': product['description'],
        'price': price['unit_amount'] / 100,
    }
    return product_details  


def create_checkout_session(cart, customer_email):
    line_items = []
    for item in cart:
        prices = stripe.Price.list(product=item['id'])
        price = prices.data[0] 
        line_items.append({
            'price': price.id,
            'quantity': item['quantity'],
        })
        
    checkout_session = stripe.checkout.Session.create(
        line_items=line_items,
        payment_method_types=['card'],
        mode='payment',
        customer_creation='always',
        success_url=f'{settings.BASE_URL}{reverse("payment_successful")}?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{settings.BASE_URL}{reverse("payment_cancelled")}',
        customer_email=customer_email,
    )
    return checkout_session

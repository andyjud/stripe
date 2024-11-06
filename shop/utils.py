import stripe

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

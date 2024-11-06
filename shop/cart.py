import stripe
from django.conf import settings
from .utils import get_product_details

stripe.api_key = settings.STRIPE_SECRET_KEY

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart_session = self.session.get(settings.CART_SESSION_ID)
        if not cart_session:
            cart_session = self.session[settings.CART_SESSION_ID] = {}
            
        self.cart_session = cart_session 
        
    def __iter__(self):
        for product_id, item in self.cart_session.items():
            product = stripe.Product.retrieve(product_id)
            product_details = get_product_details(product)
            
            yield {
                'id': product_id,
                'image': product_details['image'], 
                'name': product_details['name'],
                'price': product_details['price'],
                'quantity': item['quantity'],
                'total_price': product_details['price'] * item['quantity'],
            }
            
    def __len__(self):
        return sum(item['quantity'] for item in self.cart_session.values())
    
    def save(self):
        self.session.modified = True
        
    def add(self, product_id, quantity=1):  
        self.cart_session[product_id] = {
            'quantity': quantity,
        }
        self.save()
        
    def remove(self, product_id):
        if product_id in self.cart_session:
            del self.cart_session[product_id]
            self.save()
            
    def get_total_cost(self):
        return sum(product_item['total_price'] for product_item in self)

import stripe
from django.conf import settings
from .utils import get_product_details
import uuid

stripe.api_key = settings.STRIPE_SECRET_KEY

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart_session = self.session.get(settings.CART_SESSION_ID)
        if not cart_session:
            cart_session = self.session[settings.CART_SESSION_ID] = {}
            
        self.cart_session = cart_session 
        
    def __iter__(self):
        for item_id, item in self.cart_session.items():
            product = stripe.Product.retrieve(item['product_id'])
            product_details = get_product_details(product, quality=item['quality'])
            
            yield {
                'id': item_id,
                'product_id': product.id,  
                'image': item['image'], 
                'name': product_details['name'],
                'description': product_details['description'],
                'price_in_cent': product_details['price_in_cent'],
                'price': product_details['price'],
                'quantity': item['quantity'],
                'total_price': product_details['price'] * item['quantity'],
                'color': item['color'],
                'size': item['size'],
                'quality': item['quality']
            }
            
    def __len__(self):
        return sum(item['quantity'] for item in self.cart_session.values())
    
    def save(self):
        self.session.modified = True
        
    def add(self, product_id, quantity=1, color=None, size=None, quality=None, image=None, item_id=None): 
        if not item_id:
            item_id = str(uuid.uuid4())
            while item_id in self.cart_session:
                item_id = str(uuid.uuid4())
            
        if item_id in self.cart_session: 
            self.cart_session[item_id]['quantity'] = quantity
        else:
            self.cart_session[item_id] = {
                'product_id': product_id,
                'quantity': quantity,
                'color': color,
                'size': size,
                'quality': quality,
                'image': image,
            }
        self.save()
        
    def remove(self, product_id):
        if product_id in self.cart_session:
            del self.cart_session[product_id]
            self.save()
            
    def get_total_cost(self):
        return sum(product_item['total_price'] for product_item in self)

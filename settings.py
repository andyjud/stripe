from environ import Env
env = Env()
env.read_env()

BASE_URL = "http://localhost:8000"

STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY_TEST', default="secret")
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default="webhook")

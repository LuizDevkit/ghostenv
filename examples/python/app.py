import os
DATABASE_URL = os.getenv("DATABASE_URL")
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY", "test")
DEBUG = os.environ["DEBUG"]

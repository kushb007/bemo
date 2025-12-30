from flask import Flask, jsonify, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from authlib.integrations.flask_client import OAuth
from os import environ as env
import os
from dotenv import load_dotenv, find_dotenv
import io
import stripe

# Load environment variables from .env file in the same directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    ENV_FILE = find_dotenv()
    if ENV_FILE:
        load_dotenv(ENV_FILE)

app = Flask(__name__)
app.config['SECRET_KEY'] = env.get("APP_SECRET_KEY")

# Use absolute path for database to ensure consistency across scripts
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')

app.config['UPLOAD_FOLDER'] = os.getcwd()+'/bemo/static/'
print("UPLOAD_FOLDER",app.config['UPLOAD_FOLDER'])
app.config['AUTH0_CLIENT_ID'] = env.get("AUTH0_CLIENT_ID")
app.config['AUTH0_CLIENT_SECRET'] = env.get("AUTH0_CLIENT_SECRET")
app.config['AUTH0_DOMAIN'] = env.get("AUTH0_DOMAIN")
app.config['SQUARE_ACCESS_TOKEN'] = env.get("SQUARE_ACCESS_TOKEN")
app.config['STRIPE_API_KEY'] = env.get("STRIPE_API_KEY")
stripe.api_key = app.config['STRIPE_API_KEY']

app.config['CACHE_TYPE'] = 'SimpleCache'  # or 'RedisCache' for Redis
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # Cache timeout in seconds
cache = Cache(app)
db = SQLAlchemy(app)
oauth = OAuth(app)

app.app_context().push()

from bemo import routes
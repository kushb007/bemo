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

# Check for DATABASE_URL environment variable (for CockroachDB/Postgres)
# If not found, fall back to local SQLite
uri = env.get('DATABASE_URL')
if uri and uri.startswith('postgresql://'):
    # SQLAlchemy requires 'cockroachdb://' to use the correct dialect
    uri = uri.replace('postgresql://', 'cockroachdb://')

app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///' + os.path.join(basedir, 'site.db')

# Handle CockroachDB specific configuration if needed
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('cockroachdb'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

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
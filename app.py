from flask import Flask
from worker import redis_url
from flask_sse import sse

app = Flask(__name__)
app.config["REDIS_URL"] = redis_url
app.register_blueprint(sse, url_prefix='/stream')
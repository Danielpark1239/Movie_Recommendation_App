from flask import Flask
from worker import redis_url

app = Flask(__name__)
app.config["REDIS_URL"] = redis_url

if __name__ == '__main__':
    app.run()
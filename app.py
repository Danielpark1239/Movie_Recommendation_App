from flask import Flask
from celery import Celery, Task
from dotenv import load_dotenv
import os

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

# Load environment variables and run app
load_dotenv()
app = Flask(__name__)
# set up celery
app.config.from_mapping(
    CELERY=dict(
        broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
        result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379'),
        imports=['scraping.scraper']
    )
)
celery_app = celery_init_app(app)

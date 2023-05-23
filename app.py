from flask import Flask
from celery import Celery, Task
from dotenv import load_dotenv
import os
import redis

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
if os.getenv('APP_MODE') == 'production':
    app.config.from_mapping(
        CELERY=dict(
            broker_url=os.getenv('BROKER_URL', ''),
            broker_transport_options={
                'region': 'us-east-1',
                'predefined_queues': {
                    'celery': {
                        'url': os.getenv('SQS_URL', ''),
                        'access_key_id':  os.getenv('AWS_ACCESS_KEY', ''),
                        'secret_access_key': os.getenv('AWS_SECRET_KEY', ''),
                    }
                }
            },
            result_backend=os.getenv('REDIS_URL', ''),
            imports=['scraping.scraper']
        )
    )
else:
    app.config.from_mapping(
        CELERY=dict(
            broker_url='redis://localhost:6379',
            result_backend='redis://localhost:6379',
            imports=['scraping.scraper']
        )
    )
celery_app = celery_init_app(app)

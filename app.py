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
    if os.getenv('APP_MODE') == 'production':
        celery_app.config_from_object(app.config["PROD"])
    else:
        celery_app.config_from_object(app.config["DEBUG"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

# Load environment variables and run app
load_dotenv()
app = Flask(__name__)
# set up celery
if os.getenv('APP_MODE') == 'production':
    app.config.from_mapping(
        PROD=dict(
            broker_url=os.getenv('REDIS_URL', ''),
            result_backend=os.getenv('REDIS_URL', ''),
            imports=['scraping.scraper']
        )
    )

    # Old config for Elastic Beanstalk
    # app.config.from_mapping(
    #     PROD=dict(
    #         broker_url=f"sqs://{os.getenv('AWS_ACCESS_KEY', '')}:{os.getenv('AWS_SECRET_KEY')}@",
    #         broker_transport_options={
    #             'region': 'us-east-1',
    #             'predefined_queues': {
    #                 'celery': {
    #                     'url': os.getenv('SQS_URL', ''),
    #                     'access_key_id':  os.getenv('AWS_ACCESS_KEY', ''),
    #                     'secret_access_key': os.getenv('AWS_SECRET_KEY', ''),
    #                 }
    #             }
    #         },
    #         result_backend=os.getenv('REDIS_URL', ''),
    #         imports=['scraping.scraper']
    #     )
    # )
else:
    app.config.from_mapping(
        DEBUG=dict(
            broker_url=os.getenv('LOCAL_REDIS_URL', ''),
            result_backend=os.getenv('LOCAL_REDIS_URL', ''),
            imports=['scraping.scraper']
        )
    )
celery_app = celery_init_app(app)

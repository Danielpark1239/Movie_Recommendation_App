web: gunicorn --workers=1 main:app
worker: celery -A main.celery_app worker --loglevel=INFO -E
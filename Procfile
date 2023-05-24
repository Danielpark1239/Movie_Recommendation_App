web: gunicorn --timeout 120 --workers=1 main:app
worker: celery -A main.celery_app worker --loglevel=info
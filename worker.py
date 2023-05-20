import os
import redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

listen = ['high', 'default', 'low']

# Initialize Redis for bg worker queue
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        load_dotenv()
        worker = Worker(map(Queue, listen))
        worker.work()
import os

wsgi_app = "src.main:create_app()"
bind = "0.0.0.0:8080"
workers = 1
threads = int(os.getenv("GTHREADS", "1"))
worker_class = os.getenv("WORKER_CLASS", "sync")
timeout = 30
loglevel = "debug"
keepalive = 2
max_requests = 600
max_requests_jitter = 60
preload_app = False

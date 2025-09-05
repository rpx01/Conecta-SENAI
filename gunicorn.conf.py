import os

# Bind to host/port pulled from PORT env var for flexibility
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"

# Worker settings tuned to avoid OOM and excessive concurrency
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
threads = int(os.getenv("GTHREADS", "1"))
worker_class = os.getenv("WORKER_CLASS", "sync")

timeout = 30
keepalive = 2
max_requests = 600
max_requests_jitter = 60
preload_app = False

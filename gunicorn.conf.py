import multiprocessing
import os

# Bind to host/port pulled from PORT env var for flexibility
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"

# Allow customizing worker count via env while providing sane default
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Set a reasonable default timeout; configurable through env var
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))

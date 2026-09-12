# Gunicorn configuration for production deployment
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WEB_CONCURRENCY', 2))
worker_class = 'uvicorn.workers.UvicornWorker'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout settings - CRITICAL FOR TENSORFLOW LOADING
timeout = 120  # 2 minutes for worker timeout (handles model loading)
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'annadata-saathi-api'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Preload app to save memory and speed up worker spawning
preload_app = True

# Worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print(" Gunicorn master process starting...")

def when_ready(server):
    """Called just after the server is started."""
    print(" Gunicorn server is ready. Spawning workers...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print(" Reloading workers...")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    print(f" Worker {worker.pid} received interrupt signal")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    print(f" Worker {worker.pid} aborted (likely timeout)")

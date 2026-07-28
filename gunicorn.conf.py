# Gunicorn Production Configuration for Prescription Extractor API
import os
import multiprocessing

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts & Keep-Alive for OCR workloads
timeout = 120
keepalive = 5

# Logging configuration
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)ss'

# Security & Process management
max_requests = 1000
max_requests_jitter = 50
preload_app = True

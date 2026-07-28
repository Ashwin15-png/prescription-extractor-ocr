# Gunicorn Production Configuration for Prescription Extractor API
import os
import multiprocessing

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
# Default to 2 workers to stay well within cloud memory limits (e.g., Render 512MB RAM)
workers = int(os.getenv('WEB_CONCURRENCY', '2'))
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts & Keep-Alive for heavy OCR workloads
timeout = 120
keepalive = 5

# Logging configuration
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)ss'

# Memory safety settings
max_requests = 1000
max_requests_jitter = 50
preload_app = False  # Avoid sharing OpenCV/Tesseract state across forks

import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read Broker and Backend URLs from environment variables
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")  # Optional result backend

# Initialize Celery
celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat / Periodic Tasks Schedule
celery_app.conf.beat_schedule = {
    "run-every-minute-print-hello": {
        "task": "celery_app.print_hello",
        "schedule": crontab(minute="*"),  # runs every minute
    },
}


# Example Worker Task (Run asynchronously in the background)
@celery_app.task(name="celery_app.send_email_task")
def send_email_task(email: str, subject: str, message: str):
    print(f"Celery: Starting task send_email_task to {email}...")
    import time
    time.sleep(2)
    print(f"Celery: Email successfully sent to {email}!")
    return {"status": "success", "email": email}


# Example Beat Task (Run periodically on schedule)
@celery_app.task(name="celery_app.print_hello")
def print_hello():
    print("Celery Beat: Hello! This periodic task runs every minute.")
    return "printed hello successfully"

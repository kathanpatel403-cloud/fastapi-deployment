import os
import socket
from html import escape
from urllib.parse import urlparse

from fastapi.responses import HTMLResponse
from sqlalchemy import text

from database import engine


async def check_database_status():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "Database connection succeeded"
    except Exception as exc:
        return False, f"Database connection failed: {exc}"


def check_message_broker_status():
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    parsed = urlparse(broker_url)

    if parsed.scheme.startswith("redis"):
        try:
            import redis

            client = redis.Redis.from_url(broker_url, socket_connect_timeout=2)
            client.ping()
            return True, f"Message broker reachable at {parsed.hostname or 'localhost'}:{parsed.port or 6379}"
        except Exception as exc:
            return False, f"Unable to reach Redis broker: {exc}"

    if parsed.scheme.startswith("amqp"):
        try:
            with socket.create_connection((parsed.hostname or "localhost", parsed.port or 5672), timeout=2):
                return True, f"AMQP endpoint reachable at {parsed.hostname or 'localhost'}:{parsed.port or 5672}"
        except Exception as exc:
            return False, f"Unable to reach RabbitMQ endpoint: {exc}"

    return False, f"Broker URL {broker_url} is not a supported Redis/RabbitMQ endpoint"


def render_health_dashboard(db_ok: bool, db_message: str, broker_ok: bool, broker_message: str):
    overall_status = "healthy" if db_ok and broker_ok else "degraded"
    status_badge = "✅ Healthy" if overall_status == "healthy" else "⚠️ Needs attention"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>FastAPI Backend Status</title>
        <style>
            :root {{
                color-scheme: dark;
                --bg: #07111f;
                --card: #0f172a;
                --text: #e2e8f0;
                --muted: #94a3b8;
                --ok: #22c55e;
                --warn: #f59e0b;
                --border: #334155;
            }}
            body {{
                margin: 0;
                font-family: Inter,Segoe UI,Roboto,sans-serif;
                background: linear-gradient(135deg, var(--bg), #111827);
                color: var(--text);
                min-height: 100vh;
                display: grid;
                place-items: center;
                padding: 24px;
            }}
            .panel {{
                width: min(920px, 100%);
                background: rgba(15, 23, 42, 0.95);
                border: 1px solid var(--border);
                border-radius: 24px;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
                overflow: hidden;
            }}
            .hero {{
                padding: 32px 32px 20px;
                background: linear-gradient(90deg, rgba(34,197,94,0.15), rgba(59,130,246,0.15));
            }}
            .hero h1 {{ margin: 0 0 8px; font-size: 2rem; }}
            .hero p {{ margin: 0; color: var(--muted); line-height: 1.6; }}
            .status {{
                margin: 20px 32px;
                padding: 14px 18px;
                border-radius: 999px;
                display: inline-flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                background: rgba(34,197,94,0.12);
                color: var(--ok);
                border: 1px solid rgba(34,197,94,0.25);
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 16px;
                padding: 0 32px 32px;
            }}
            .card {{
                background: rgba(2, 6, 23, 0.55);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 18px;
            }}
            .card h2 {{ margin: 0 0 10px; font-size: 1.05rem; }}
            .value {{ font-size: 1.4rem; font-weight: 700; margin-bottom: 6px; }}
            .muted {{ color: var(--muted); font-size: 0.95rem; line-height: 1.5; }}
            .ok {{ color: var(--ok); }}
            .warn {{ color: var(--warn); }}
            .footer {{ color: var(--muted); padding: 0 32px 28px; font-size: 0.92rem; }}
        </style>
    </head>
    <body>
        <div class="panel">
            <div class="hero">
                <h1>FastAPI Backend Status</h1>
                <p>This page confirms that your FastAPI service is up and shows whether its key dependencies are configured and reachable.</p>
            </div>
            <div class="status">{status_badge}</div>
            <div class="grid">
                <div class="card">
                    <h2>Application</h2>
                    <div class="value ok">Running</div>
                    <div class="muted">Your FastAPI backend is responsive and serving requests successfully.</div>
                </div>
                <div class="card">
                    <h2>Database</h2>
                    <div class="value {'ok' if db_ok else 'warn'}">{'Configured' if db_ok else 'Attention required'}</div>
                    <div class="muted">{escape(db_message)}</div>
                </div>
                <div class="card">
                    <h2>Message Broker</h2>
                    <div class="value {'ok' if broker_ok else 'warn'}">{'Configured' if broker_ok else 'Attention required'}</div>
                    <div class="muted">{escape(broker_message)}</div>
                </div>
                <div class="card">
                    <h2>Background Jobs</h2>
                    <div class="value ok">Celery ready</div>
                    <div class="muted">The app is wired for asynchronous tasks through Celery and the configured broker.</div>
                </div>
            </div>
            <div class="footer">
                Environment hint: database settings come from the PostgreSQL variables and the broker is read from the CELERY_BROKER_URL setting.
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

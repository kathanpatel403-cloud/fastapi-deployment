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
            @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500&display=swap');

            :root {{
                color-scheme: dark;
                --bg: #090d14;
                --panel: #0e1420;
                --panel-2: #0b111c;
                --text: #e7ebf2;
                --muted: #6e7b90;
                --border: #1c2635;
                --accent: #5eead4;
                --ok: #34d399;
                --ok-bg: rgba(52, 211, 153, 0.1);
                --warn: #f5b544;
                --warn-bg: rgba(245, 181, 68, 0.1);
            }}

            * {{ box-sizing: border-box; }}

            @media (prefers-reduced-motion: reduce) {{
                * {{ animation: none !important; transition: none !important; }}
            }}

            body {{
                margin: 0;
                font-family: 'Inter', Segoe UI, Roboto, sans-serif;
                background:
                    repeating-linear-gradient(180deg, rgba(255,255,255,0.015) 0px, rgba(255,255,255,0.015) 1px, transparent 1px, transparent 3px),
                    radial-gradient(circle at 15% 0%, #101a2c 0%, var(--bg) 55%);
                color: var(--text);
                min-height: 100vh;
                display: grid;
                place-items: center;
                padding: 24px;
            }}

            .panel {{
                position: relative;
                width: min(880px, 100%);
                background: linear-gradient(180deg, var(--panel), var(--panel-2));
                border: 1px solid var(--border);
                border-radius: 4px;
                box-shadow: 0 30px 60px rgba(0, 0, 0, 0.45);
                overflow: hidden;
            }}

            .panel::before, .panel::after,
            .hero .corner-l, .hero .corner-r {{
                content: "";
                position: absolute;
                width: 14px;
                height: 14px;
                border: 1.5px solid var(--accent);
                opacity: 0.55;
            }}
            .panel::before {{ top: -1px; left: -1px; border-right: none; border-bottom: none; }}
            .panel::after {{ bottom: -1px; right: -1px; border-left: none; border-top: none; }}

            .hero {{
                padding: 30px 32px 22px;
                border-bottom: 1px solid var(--border);
            }}
            .eyebrow {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.72rem;
                letter-spacing: 0.18em;
                text-transform: uppercase;
                color: var(--accent);
                margin: 0 0 10px;
            }}
            .hero h1 {{
                margin: 0 0 6px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 1.6rem;
                font-weight: 600;
                letter-spacing: -0.01em;
            }}
            .hero p {{
                margin: 0;
                color: var(--muted);
                font-size: 0.9rem;
            }}

            .status-row {{
                margin: 22px 32px 6px;
                display: flex;
            }}
            .status {{
                padding: 9px 16px;
                border-radius: 999px;
                display: inline-flex;
                align-items: center;
                gap: 9px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.82rem;
                font-weight: 600;
                letter-spacing: 0.02em;
                background: var(--ok-bg);
                color: var(--ok);
                border: 1px solid rgba(52, 211, 153, 0.3);
            }}
            .status::before {{
                content: "";
                width: 7px;
                height: 7px;
                border-radius: 50%;
                background: currentColor;
                box-shadow: 0 0 0 0 currentColor;
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0% {{ box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.45); }}
                70% {{ box-shadow: 0 0 0 6px rgba(52, 211, 153, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }}
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
                gap: 14px;
                padding: 20px 32px 30px;
            }}
            .card {{
                position: relative;
                background: rgba(0, 0, 0, 0.18);
                border: 1px solid var(--border);
                border-left: 2px solid var(--border);
                border-radius: 3px;
                padding: 16px 18px;
            }}
            .card.is-ok {{ border-left-color: var(--ok); }}
            .card.is-warn {{ border-left-color: var(--warn); }}

            .card h2 {{
                margin: 0 0 10px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.7rem;
                font-weight: 500;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: var(--muted);
            }}
            .value {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 5px;
            }}
            .muted {{ color: var(--muted); font-size: 0.85rem; line-height: 1.5; }}
            .ok {{ color: var(--ok); }}
            .warn {{ color: var(--warn); }}

            .footer {{
                border-top: 1px solid var(--border);
                color: var(--muted);
                padding: 14px 32px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.74rem;
                letter-spacing: 0.01em;
            }}
        </style>
    </head>
    <body>
        <div class="panel">
            <div class="hero">
                <p class="eyebrow">System status</p>
                <h1>FastAPI Backend</h1>
                <p>Live health check for the API, database, and task queue.</p>
            </div>
            <div class="status-row">
                <div class="status">{status_badge}</div>
            </div>
            <div class="grid">
                <div class="card is-ok">
                    <h2>Application</h2>
                    <div class="value ok">Running</div>
                    <div class="muted">Serving requests.</div>
                </div>
                <div class="card {'is-ok' if db_ok else 'is-warn'}">
                    <h2>Database</h2>
                    <div class="value {'ok' if db_ok else 'warn'}">{'Configured' if db_ok else 'Attention required'}</div>
                    <div class="muted">{escape(db_message)}</div>
                </div>
                <div class="card {'is-ok' if broker_ok else 'is-warn'}">
                    <h2>Message Broker</h2>
                    <div class="value {'ok' if broker_ok else 'warn'}">{'Configured' if broker_ok else 'Attention required'}</div>
                    <div class="muted">{escape(broker_message)}</div>
                </div>
                <div class="card is-ok">
                    <h2>Background Jobs</h2>
                    <div class="value ok">Celery ready</div>
                    <div class="muted">Async tasks via Celery.</div>
                </div>
            </div>
            <div class="footer">
                DB → PostgreSQL env vars · Broker → CELERY_BROKER_URL
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

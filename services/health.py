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
    <title>FastAPI · System Status</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;1,9..144,300&family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&display=swap">
    <style>
        :root {{
            color-scheme: dark;
            --bg: #0a0a0b;
            --surface: #111114;
            --surface-2: #16161a;
            --surface-3: #1c1c22;
            --text: #f4f4f5;
            --text-2: #d4d4d8;
            --muted: #8a8a94;
            --subtle: #52525b;
            --border: #23232a;
            --border-strong: #2e2e37;
            --accent: #a3e635;
            --accent-soft: rgba(163, 230, 53, 0.12);
            --ok: #86efac;
            --ok-bg: rgba(134, 239, 172, 0.06);
            --ok-border: rgba(134, 239, 172, 0.2);
            --warn: #fcd34d;
            --warn-bg: rgba(252, 211, 77, 0.06);
            --warn-border: rgba(252, 211, 77, 0.2);
        }}

        * {{ box-sizing: border-box; }}

        @media (prefers-reduced-motion: reduce) {{
            * {{ animation: none !important; transition: none !important; }}
        }}

        html, body {{ height: 100%; }}

        body {{
            margin: 0;
            font-family: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 15px;
            line-height: 1.5;
            color: var(--text);
            background: var(--bg);
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 40px 24px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
        }}

        /* Ambient background */
        body::before {{
            content: "";
            position: fixed;
            inset: 0;
            background:
                radial-gradient(ellipse 90% 60% at 50% -20%, rgba(163, 230, 53, 0.06), transparent 60%),
                radial-gradient(ellipse 50% 40% at 100% 100%, rgba(163, 230, 53, 0.03), transparent 60%);
            pointer-events: none;
            z-index: 0;
        }}

        body::after {{
            content: "";
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(rgba(255,255,255,0.012) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.012) 1px, transparent 1px);
            background-size: 56px 56px;
            pointer-events: none;
            z-index: 0;
            mask-image: radial-gradient(ellipse 60% 50% at 50% 40%, black, transparent 85%);
        }}

        .shell {{
            position: relative;
            width: min(960px, 100%);
            z-index: 1;
        }}

        /* Top brand row */
        .brand {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 28px;
            padding: 0 4px;
        }}
        .brand-mark {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-family: 'Geist Mono', monospace;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 0.08em;
            color: var(--text-2);
        }}
        .brand-logo {{
            width: 22px;
            height: 22px;
            border: 1px solid var(--border-strong);
            border-radius: 6px;
            display: grid;
            place-items: center;
            background: var(--surface-2);
        }}
        .brand-logo::before {{
            content: "";
            width: 8px;
            height: 8px;
            background: var(--accent);
            border-radius: 2px;
            box-shadow: 0 0 12px var(--accent);
        }}
        .brand-meta {{
            font-family: 'Geist Mono', monospace;
            font-size: 11px;
            color: var(--muted);
            letter-spacing: 0.06em;
        }}

        /* Main card */
        .panel {{
            position: relative;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            overflow: hidden;
            box-shadow:
                0 50px 100px -30px rgba(0, 0, 0, 0.7),
                0 1px 0 rgba(255, 255, 255, 0.03) inset;
        }}

        /* Hero */
        .hero {{
            padding: 48px 48px 40px;
            border-bottom: 1px solid var(--border);
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 32px;
            align-items: end;
        }}
        .eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-family: 'Geist Mono', monospace;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--muted);
            margin: 0 0 20px;
        }}
        .eyebrow::before {{
            content: "";
            width: 16px;
            height: 1px;
            background: var(--border-strong);
        }}
        .hero h1 {{
            margin: 0 0 14px;
            font-family: 'Fraunces', 'Times New Roman', serif;
            font-size: clamp(2.2rem, 4vw, 3rem);
            font-weight: 300;
            letter-spacing: -0.02em;
            line-height: 1.02;
            color: var(--text);
        }}
        .hero h1 em {{
            font-style: italic;
            font-weight: 300;
            color: var(--accent);
        }}
        .hero p {{
            margin: 0;
            color: var(--muted);
            font-size: 15px;
            line-height: 1.6;
            max-width: 46ch;
            font-weight: 400;
        }}

        .status {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px 10px 14px;
            border-radius: 999px;
            font-family: 'Geist Mono', monospace;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 0.04em;
            background: var(--ok-bg);
            color: var(--ok);
            border: 1px solid var(--ok-border);
            white-space: nowrap;
        }}
        .status-dot {{
            position: relative;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
        }}
        .status-dot::after {{
            content: "";
            position: absolute;
            inset: -4px;
            border-radius: 50%;
            background: currentColor;
            opacity: 0.3;
            animation: pulse 2.4s ease-in-out infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(0.8); opacity: 0.3; }}
            50% {{ transform: scale(1.6); opacity: 0; }}
        }}

        /* Grid */
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1px;
            background: var(--border);
        }}
        .card {{
            position: relative;
            background: var(--surface);
            padding: 28px 28px 26px;
            transition: background 0.25s ease;
        }}
        .card:hover {{ background: var(--surface-2); }}

        .card-head {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }}
        .card-label {{
            margin: 0;
            font-family: 'Geist Mono', monospace;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--muted);
        }}
        .card-pill {{
            font-family: 'Geist Mono', monospace;
            font-size: 10px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--subtle);
            padding: 3px 7px;
            border: 1px solid var(--border);
            border-radius: 4px;
        }}

        .value {{
            font-family: 'Fraunces', serif;
            font-size: 1.55rem;
            font-weight: 300;
            letter-spacing: -0.015em;
            margin-bottom: 10px;
            color: var(--text);
            line-height: 1.1;
        }}
        .card.is-ok .value {{ color: var(--ok); }}
        .card.is-warn .value {{ color: var(--warn); }}

        .card-desc {{
            color: var(--muted);
            font-size: 13.5px;
            line-height: 1.55;
        }}

        /* Footer */
        .footer {{
            border-top: 1px solid var(--border);
            padding: 20px 48px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
            background: var(--surface-2);
        }}
        .footer-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: 'Geist Mono', monospace;
            font-size: 11.5px;
            color: var(--muted);
            letter-spacing: 0.02em;
        }}
        .footer-item strong {{
            color: var(--text-2);
            font-weight: 500;
        }}
        .footer-arrow {{
            color: var(--subtle);
        }}

        @media (max-width: 720px) {{
            body {{ padding: 24px 16px; }}
            .hero {{
                padding: 32px 28px 28px;
                grid-template-columns: 1fr;
                align-items: start;
            }}
            .hero h1 {{ font-size: 2rem; }}
            .card {{ padding: 24px; }}
            .footer {{ padding: 18px 28px; gap: 12px; }}
        }}
    </style>
</head>
<body>
    <div class="shell">
        <div class="brand">
            <div class="brand-mark">
                <div class="brand-logo"></div>
                <span>fastapi · control</span>
            </div>
            <div class="brand-meta">v1.0 · runtime</div>
        </div>

        <div class="panel">
            <div class="hero">
                <div>
                    <p class="eyebrow">System status</p>
                    <h1>All systems <em>operational.</em></h1>
                    <p>Real-time health telemetry for the API surface, primary datastore, and asynchronous task pipeline.</p>
                </div>
                <div class="status">
                    <span class="status-dot"></span>
                    {status_badge}
                </div>
            </div>

            <div class="grid">
                <div class="card is-ok">
                    <div class="card-head">
                        <p class="card-label">Application</p>
                        <span class="card-pill">API</span>
                    </div>
                    <div class="value">Running</div>
                    <div class="card-desc">Serving inbound requests.</div>
                </div>

                <div class="card {'is-ok' if db_ok else 'is-warn'}">
                    <div class="card-head">
                        <p class="card-label">Database</p>
                        <span class="card-pill">PG</span>
                    </div>
                    <div class="value">{'Configured' if db_ok else 'Attention'}</div>
                    <div class="card-desc">{escape(db_message)}</div>
                </div>

                <div class="card {'is-ok' if broker_ok else 'is-warn'}">
                    <div class="card-head">
                        <p class="card-label">Message Broker</p>
                        <span class="card-pill">MQ</span>
                    </div>
                    <div class="value">{'Configured' if broker_ok else 'Attention'}</div>
                    <div class="card-desc">{escape(broker_message)}</div>
                </div>

                <div class="card is-ok">
                    <div class="card-head">
                        <p class="card-label">Background Jobs</p>
                        <span class="card-pill">CEL</span>
                    </div>
                    <div class="value">Celery ready</div>
                    <div class="card-desc">Async tasks dispatched via Celery workers.</div>
                </div>
            </div>

            <div class="footer">
                <div class="footer-item">
                    <strong>DB</strong>
                    <span class="footer-arrow">→</span>
                    <span>PostgreSQL env vars</span>
                </div>
                <div class="footer-item">
                    <strong>Broker</strong>
                    <span class="footer-arrow">→</span>
                    <span>CELERY_BROKER_URL</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>

    """
    
    return HTMLResponse(content=html)

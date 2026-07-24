"""
Obsidian Armory — Flask backend
--------------------------------
Serves the four site pages and a single write endpoint, /api/reserve,
that stores reservation submissions in Supabase.

Payment is intentionally NOT wired up yet — this endpoint only records
intent to order. See README.md for setup and the payment TODO.
"""

import os
import re
import secrets
from datetime import datetime, timezone

from flask import Flask, render_template, request, jsonify, session, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")  # service role key, server-side only

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------------
# Rate limiting — protects the write endpoint from spam/abuse
# ---------------------------------------------------------------------------
limiter = Limiter(get_remote_address, app=app, default_limits=[])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_UNITS = {"Red Igris", "White Mane", "Shadow Beast", "Eco Builder"}


# ---------------------------------------------------------------------------
# CSRF — double-submit token, issued per session, checked on the API route
# ---------------------------------------------------------------------------
@app.before_request
def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(24)


def csrf_token():
    return session.get("csrf_token", "")


app.jinja_env.globals["csrf_token"] = csrf_token


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/armory")
def armory():
    return render_template("armory.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/order")
def order():
    return render_template("order.html")


# ---------------------------------------------------------------------------
# API — reservation intake
# ---------------------------------------------------------------------------
@app.route("/api/reserve", methods=["POST"])
@limiter.limit("5 per minute")
def api_reserve():
    # CSRF check (double-submit cookie/session pattern)
    sent_token = request.headers.get("X-CSRF-Token", "")
    if not sent_token or sent_token != session.get("csrf_token"):
        abort(403, description="Invalid or missing CSRF token.")

    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    account_number = (data.get("account_number") or "").strip() or None
    unit = (data.get("unit") or "").strip() or None
    price = data.get("price")

    # ---- validation ----
    if not full_name or len(full_name) > 200:
        return jsonify(error="Please enter a valid name."), 400
    if not email or not EMAIL_RE.match(email) or len(email) > 200:
        return jsonify(error="Please enter a valid email address."), 400
    if not phone or len(phone) < 6 or len(phone) > 30:
        return jsonify(error="Please enter a valid phone number."), 400
    if unit and unit not in VALID_UNITS:
        return jsonify(error="Unrecognized unit."), 400

    try:
        price_value = float(price) if price not in (None, "") else None
    except (TypeError, ValueError):
        price_value = None

    record = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "account_number": account_number,
        "unit": unit,
        "price": price_value,
        "status": "pending_payment",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if supabase is None:
        # Backend is reachable but not yet connected to a Supabase project.
        return jsonify(error="Reservations aren't being stored yet — Supabase isn't connected on this deployment."), 503

    try:
        result = supabase.table("reservations").insert(record).execute()
        inserted = result.data[0] if result.data else {}
        reference = inserted.get("id", "pending")
    except Exception as exc:  # noqa: BLE001 — surface a generic message, log the real one
        app.logger.error("Supabase insert failed: %s", exc)
        return jsonify(error="Could not save your reservation right now. Please try again shortly."), 500

    return jsonify(success=True, reference=reference), 201


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------
@app.errorhandler(429)
def rate_limited(e):
    return jsonify(error="Too many requests. Please wait a moment and try again."), 429


@app.errorhandler(403)
def forbidden(e):
    return jsonify(error=str(e.description) if hasattr(e, "description") else "Forbidden"), 403


if __name__ == "__main__":
    app.run(debug=True, port=5000)
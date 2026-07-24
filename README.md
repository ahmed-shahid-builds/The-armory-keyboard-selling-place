# Obsidian Armory — Flask + Supabase

## What's here
- `app.py` — Flask app. Serves the 4 pages and one API route: `POST /api/reserve`.
- `templates/` — the 4 HTML pages (Jinja, using `url_for` for nav + assets).
- `static/` — CSS, JS, product images.
- `schema.sql` — the one table this needs (`reservations`).
- `vercel.json` — deploy config for Vercel's Python runtime.

## Local setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in the two Supabase values below
python app.py                   # http://localhost:5000
```

## Supabase setup
1. Create a project at supabase.com (or use an existing one).
2. Project Settings → API — copy the **Project URL** and the **service_role** key
   (not the `anon` key — the service role key is what lets the Flask backend
   write past Row Level Security).
3. SQL Editor → paste and run `schema.sql`. This creates the `reservations`
   table with RLS enabled and no public policies, so the table is invisible
   to anyone using the anon/public key — only your Flask server can touch it.
4. Put those two values in `.env` (or Vercel's env vars — see below).

## Deploying to Vercel
Same pattern as your accounting site:
1. Push this folder to a GitHub repo, import it in Vercel.
2. Project Settings → Environment Variables, add for this project only:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `FLASK_SECRET_KEY` (any long random string — used to sign the session
     cookie that the CSRF token rides on)
3. Deploy. `vercel.json` tells Vercel to run everything through `app.py`
   except `/static/*`, which is served directly.

## What's live vs. what's not
- **Live:** the 4 pages, and `/api/reserve` writes a row to `reservations`
  with `status = pending_payment`.
- **Not live:** actual payment. The order page says this explicitly — no
  card details are collected anywhere. When you're ready to add a payment
  provider (Stripe is the easiest fit for Flask), the natural place to hook
  in is right after the `supabase.table("reservations").insert(...)` call
  in `app.py` — create the payment session there and return its URL to the
  front end instead of a plain confirmation message.
- **Also not live:** the "Email Identifier" / "Number Identifier" fields on
  the order page are disabled placeholders for a future OTP/verification
  step. They aren't submitted to the backend yet.

## Security notes
- CSRF: a per-session token is issued on first request and injected into
  the order page. `/api/reserve` rejects any POST whose `X-CSRF-Token`
  header doesn't match the session's token.
- Rate limiting: `/api/reserve` is capped at 5 requests/minute per IP via
  `flask-limiter`, to blunt basic spam/bot submissions.
- Honeypot: the order form has a hidden `website` field. Real users never
  fill it in; bots often do. Submissions with it filled are silently
  dropped client-side.
- The Supabase **service_role key never reaches the browser** — it's only
  read from the environment inside `app.py`. Do not put it in any
  `static/` file or template.

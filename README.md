AgentBox API

Run locally
- Ensure Python 3.11+ and a virtualenv are active
- Install deps: `pip install -r requirements.txt`
- Start server (dev): `python main.py`
- Docs: visit `http://127.0.0.1:8000/docs`

Endpoints (stubs)
- POST /v1/inbox
  - Body: { user, subdomain, domain }
  - Note: Domain must be registered with the platform to be used

- POST /v1/email
  - Body: { to: string[], subject: string, body: string, inbox_id?: string, in_reply_to_id?: string }

- GET /v1/email?id={id}
  - Returns the email with the given id

- GET /v1/email/thread?id={id}
  - Returns the thread for the email with id

Notes
- These endpoints are stubbed and return placeholder data
- CORS is open for local development; tighten for production
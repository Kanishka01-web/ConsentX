# frontend/

Not built yet — this is your frontend teammate's folder.

Per Step 8 of the plan, once the backend API is stable you hand them:
- The API base URL and endpoints (see backend/app/routes)
- Request JSON shape for each endpoint (see backend/app/schemas.py)
- Response JSON shape for each endpoint
- Error format (FastAPI's default `{"detail": "..."}`)

Reference endpoints currently available:
- `POST /users/` — register a user
- `GET /users/{user_id}` — fetch a user
- `POST /consent/` — create a consent record
- `GET /consent/user/{user_id}` — list a user's consent records
- `GET /consent/{consent_id}` — fetch one consent record
- `POST /consent/{consent_id}/revoke` — revoke a consent record
- `POST /ai/analyze` — analyze consent text (risk, reason, recommendation)

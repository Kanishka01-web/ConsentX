from fastapi import FastAPI

from .database import Base, engine
from .routes import users, consent, ai, audit, auth, access

# Creates consentx.db (SQLite) with the users/consents tables on first run.
# Swap DATABASE_URL in .env for Postgres etc. when you outgrow this.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ConsentX Backend")

app.include_router(users.router)
app.include_router(consent.router)
app.include_router(ai.router)
app.include_router(audit.router)
app.include_router(auth.router)
app.include_router(access.router)

@app.get("/")
def root():
    return {
        "message": "ConsentX backend is running"
    }

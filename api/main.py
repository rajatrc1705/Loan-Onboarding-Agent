from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import agent, customer, livekit, rfi
from .db import init_db

app = FastAPI(title="Onboarding Control Tower API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    print("Trying to initialize db")
    init_db()
    print("Initialized db")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(rfi.router, prefix="/rfi", tags=["rfi"])
app.include_router(customer.router, prefix="/c", tags=["customer"])
app.include_router(livekit.router, prefix="/livekit", tags=["livekit"])
app.include_router(agent.router, prefix="/agent", tags=["agent"])


@app.post("/admin/init-db")
def init_db_endpoint() -> dict:
    init_db()
    return {"status": "initialized"}

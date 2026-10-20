import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.onboarding import router
from app.psql_db import Base, engine

## loading the env keys
load_dotenv()


def create_app(initialize_db: bool = True) -> FastAPI:
    session_secret = os.getenv("SESSION_SECRET_KEY")

    if not session_secret:
        raise RuntimeError(
            "SESSION_SECRET_KEY is missing. "
            "Set it in your .env file before starting the application."
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if initialize_db:
            from app.models.user import User  # noqa: F401

            Base.metadata.create_all(bind=engine)
        yield

    app = FastAPI(
        title="Research Pulse",
        lifespan=lifespan,
    )
    app.include_router(router)
    app.include_router(health_router)

    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret,
        https_only=False,
        same_site="lax",
    )

    return app


app = create_app()

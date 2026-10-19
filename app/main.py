from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.onboarding import router
from app.psql_db import Base, engine


def create_app(initialize_db: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if initialize_db:
            # Import models so SQLAlchemy registers their tables.
            from app.models.user import User  # noqa: F401

            Base.metadata.create_all(bind=engine)
        yield

    app = FastAPI(
        title="Research Pulse",
        lifespan=lifespan,
    )
    app.include_router(router)

    return app


app = create_app()

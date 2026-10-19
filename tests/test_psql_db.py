"""Test the connection to the local PostgreSQL database."""

import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

## load the env variables
load_dotenv()


def main() -> None:
    # Build the URL safely, even if the password has special characters.
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("PSQL_DB_USER"),
        password=os.getenv("PSQL_DB_PASSWORD"),
        host=os.getenv("PSQL_DB_HOST"),
        port=os.getenv("PSQL_DB_PORT"),
        database=os.getenv("PSQL_DB_NAME"),
    )

    # Create an engine. It manages database connections.
    engine = create_engine(database_url, pool_pre_ping=True)

    try:
        # Open a connection and run a simple SQL query.
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database(), current_user"))
            database, user = result.one()

            print(f"Connected successfully to: {database}")
            print(f"Authenticated as: {user}")

    finally:
        # Release the engine's connection-pool resources.
        engine.dispose()


if __name__ == "__main__":
    main()

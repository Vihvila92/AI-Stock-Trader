from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
import os
import secrets
import json
from pymongo import MongoClient

# 📌 Management database password is stored persistently
password_file = "/app/management_password.txt"

if os.path.exists(password_file):
    with open(password_file, "r") as f:
        db_password = f.read().strip()
else:
    # Use environment variable if available, otherwise generate a new password
    db_password = os.getenv("POSTGRES_PASSWORD", secrets.token_urlsafe(16))

    # Store the password in a file to keep it persistent across restarts
    with open(password_file, "w") as f:
        f.write(db_password)

# 📌 Management database connection (persistent)
MANAGEMENT_DB_URL = f"postgresql://management_user:{db_password}@db:5432/management"
management_engine = create_engine(MANAGEMENT_DB_URL, pool_size=20, max_overflow=10)
ManagementSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=management_engine)

metadata = MetaData()

# 📌 Provides a persistent management database connection
def get_management_db():
    db = ManagementSessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_event(db, level: str, source: str, message: str, metadata: dict = None):
    """Log an event into the logs table in the database."""
    db.execute(text("""
        INSERT INTO logs (level, source, message, metadata)
        VALUES (:level, :source, :message, :metadata::json)
    """), {
        "level": level,
        "source": source,
        "message": message,
        "metadata": None if metadata is None else json.dumps(metadata)
    })
    db.commit()

# 📌 Dynamic database connection handling (MySQL, PostgreSQL, MongoDB)
connection_pools = {}
mongo_clients = {}
MAX_POOL_SIZE = 10  # Maximum concurrent connections per database
MAX_OVERFLOW = 5    # Additional connections allowed temporarily
TIMEOUT = 30        # Closes idle connections after timeout

def get_dynamic_db(database_name: str):
    """ Dynamically manages database connections using connection pooling. """
    management_db = ManagementSessionLocal()

    try:
        if database_name not in connection_pools and database_name not in mongo_clients:
            result = management_db.execute(
                text("""
                    SELECT type, host, port, username, password, database_name, connection_options 
                    FROM databases 
                    WHERE name = :name AND status = 'active'
                """),
                {"name": database_name}
            ).fetchone()

            if not result:
                log_event(
                    management_db,
                    level="ERROR",
                    source="database_management",
                    message=f"Database not found or inactive",
                    metadata={"database_name": database_name}
                )
                raise ValueError(f"Database '{database_name}' not found or inactive!")

            db_type, host, port, username, password, db_name, connection_options = result

            try:
                # Construct the connection string
                if db_type in ["postgresql", "mysql"]:
                    db_url = f"{db_type}://{username}:{password}@{host}:{port}/{db_name}"
                    if connection_options:
                        db_url += f"?{connection_options}"

                    connection_pools[database_name] = create_engine(
                        db_url,
                        pool_size=MAX_POOL_SIZE,
                        max_overflow=MAX_OVERFLOW,
                        pool_timeout=TIMEOUT
                    )
                    log_event(
                        management_db,
                        level="INFO",
                        source="database_management",
                        message=f"Created new database connection pool",
                        metadata={
                            "database_name": database_name,
                            "type": db_type,
                            "host": host,
                            "port": port
                        }
                    )

                elif db_type == "mongodb":
                    mongo_url = f"mongodb://{username}:{password}@{host}:{port}/{db_name}"
                    if connection_options:
                        mongo_url += f"?{connection_options}"

                    mongo_clients[database_name] = MongoClient(mongo_url)[db_name]
                    log_event(
                        management_db,
                        level="INFO",
                        source="database_management",
                        message=f"Created new MongoDB connection",
                        metadata={
                            "database_name": database_name,
                            "host": host,
                            "port": port
                        }
                    )

            except Exception as e:
                log_event(
                    management_db,
                    level="ERROR",
                    source="database_management",
                    message="Failed to create database connection",
                    metadata={
                        "database_name": database_name,
                        "error": str(e),
                        "type": db_type
                    }
                )
                raise

        # Return connection based on database type
        if database_name in connection_pools:
            Session = sessionmaker(autocommit=False, autoflush=False, bind=connection_pools[database_name])
            db = Session()
            try:
                yield db
            finally:
                db.close()

        elif database_name in mongo_clients:
            yield mongo_clients[database_name]

        else:
            log_event(
                management_db,
                level="ERROR",
                source="database_management",
                message="Database initialization failed",
                metadata={"database_name": database_name}
            )
            raise ValueError(f"Database '{database_name}' could not be initialized.")

    except Exception as e:
        log_event(
            management_db,
            level="ERROR",
            source="database_management",
            message="Database access error",
            metadata={
                "database_name": database_name,
                "error": str(e)
            }
        )
        raise
    finally:
        management_db.close()

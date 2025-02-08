from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from app.database import get_management_db
from cryptography.fernet import Fernet
import secrets
import json

router = APIRouter()

# Constants
TOKEN_EXPIRATION_MINUTES = 30

def get_encryption_key(db: Session) -> Fernet:
    """Fetch the encryption key from the database and return a Fernet instance."""
    result = db.execute(text("""
        SELECT value FROM system_settings WHERE key = 'registration_token_encryption_key'
    """)).fetchone()

    if not result:
        raise HTTPException(status_code=500, detail="Encryption key not configured")

    encryption_key = result.value.encode()  # Ensure it's in bytes
    return Fernet(encryption_key)

def log_event(db: Session, level: str, source: str, message: str, metadata: dict = None):
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

# Create table for storing registration tokens if it doesn't exist
def ensure_token_table(db: Session):
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS agent_registration_tokens (
            id SERIAL PRIMARY KEY,
            agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
            token TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()

@router.post("/agents/register")
def pre_register_agent(name: str, db: Session = Depends(get_management_db)):
    """Pre-register an agent and generate a registration token."""
    try:
        # Ensure token table exists
        ensure_token_table(db)

        # Fetch management system address and port from system settings
        settings = db.execute(text("""
            SELECT key, value FROM system_settings 
            WHERE key IN ('management_system_address', 'management_system_port')
        """)).fetchall()

        settings_dict = {row.key: row.value for row in settings}
        management_address = settings_dict.get("management_system_address")
        management_port = settings_dict.get("management_system_port")

        if not management_address or not management_port:
            raise HTTPException(status_code=500, detail="Management system address or port not configured")

        # Ensure the agent name is unique
        existing_agent = db.execute(text("SELECT id FROM agents WHERE name = :name"), {"name": name}).fetchone()
        if existing_agent:
            raise HTTPException(status_code=400, detail="Agent name already exists")

        # Insert the agent into the database with 'pending' status
        result = db.execute(text("""
            INSERT INTO agents (name, status) VALUES (:name, 'pending') RETURNING id
        """), {"name": name})
        db.commit()

        agent_id = result.fetchone()[0]
        log_event(
            db,
            level="INFO",
            source="agent_registration",
            message=f"New agent pre-registered: {name}",
            metadata={"agent_id": agent_id, "name": name}
        )

        # Fetch encryption key from the database
        encryption_key = get_encryption_key(db)

        # Generate a secure registration token
        raw_token = f"{agent_id}|{management_address}|{management_port}|{secrets.token_urlsafe(16)}"
        encrypted_token = encryption_key.encrypt(raw_token.encode())

        # Store the token in the database
        expires_at = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
        db.execute(text("""
            INSERT INTO agent_registration_tokens (agent_id, token, expires_at)
            VALUES (:agent_id, :token, :expires_at)
        """), {"agent_id": agent_id, "token": encrypted_token.decode(), "expires_at": expires_at})
        db.commit()

        log_event(
            db,
            level="INFO",
            source=f"agent:{agent_id}",
            message="Registration token generated",
            metadata={"expires_at": expires_at.isoformat()}
        )

        return {"token": encrypted_token.decode()}

    except Exception as e:
        log_event(
            db,
            level="ERROR",
            source="agent_registration",
            message="Agent registration failed",
            metadata={"name": name, "error": str(e)}
        )
        raise

@router.post("/agents/validate-token")
def validate_registration_token(token: str, db: Session = Depends(get_management_db)):
    """Validate the registration token and register the agent."""
    try:
        # Fetch encryption key
        encryption_key = get_encryption_key(db)

        # Decrypt the token
        try:
            decrypted_token = encryption_key.decrypt(token.encode()).decode()
            agent_id, address, port, random_string = decrypted_token.split("|")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid or malformed token")

        # Validate the token against the database
        result = db.execute(text("""
            SELECT id, expires_at FROM agent_registration_tokens
            WHERE agent_id = :agent_id AND token = :token
        """), {"agent_id": agent_id, "token": token}).fetchone()

        if not result or result["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Token is expired or invalid")

        # Activate the agent
        db.execute(text("""
            UPDATE agents SET status = 'active', registered_at = CURRENT_TIMESTAMP
            WHERE id = :agent_id
        """), {"agent_id": agent_id})
        db.execute(text("DELETE FROM agent_registration_tokens WHERE id = :id"), {"id": result["id"]})
        db.commit()

        log_event(
            db,
            level="INFO",
            source=f"agent:{agent_id}",
            message="Agent successfully activated",
            metadata={"address": address, "port": port}
        )

        return {
            "message": "Agent successfully registered",
            "connection_details": {
                "address": address,
                "port": port
            }
        }

    except Exception as e:
        log_event(
            db,
            level="ERROR",
            source="agent_registration",
            message="Token validation failed",
            metadata={"error": str(e)}
        )
        raise

@router.get("/agents")
def get_agents(db: Session = Depends(get_management_db)):
    """Get all registered agents."""
    log_event(
        db,
        level="INFO",
        source="agent_management",
        message="Listed all agents"
    )
    result = db.execute(text("SELECT * FROM agents"))
    return [dict(row) for row in result]

@router.get("/agents/{agent_id}")
def get_agent(agent_id: int, db: Session = Depends(get_management_db)):
    """Get agent details by ID."""
    result = db.execute(text("SELECT * FROM agents WHERE id = :id"), {"id": agent_id}).fetchone()
    if not result:
        log_event(
            db,
            level="WARNING",
            source="agent_management",
            message=f"Attempted to fetch non-existent agent",
            metadata={"agent_id": agent_id}
        )
        raise HTTPException(status_code=404, detail="Agent not found")
    
    log_event(
        db,
        level="INFO",
        source=f"agent:{agent_id}",
        message="Agent details retrieved"
    )
    return dict(result)

@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_management_db)):
    """Delete an agent."""
    log_event(
        db,
        level="INFO",
        source=f"agent:{agent_id}",
        message="Agent deleted"
    )
    db.execute(text("DELETE FROM agents WHERE id = :id"), {"id": agent_id})
    db.commit()
    return {"message": "Agent deleted"}

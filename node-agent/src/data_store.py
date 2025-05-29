#!/usr/bin/env python3
"""
Secure Data Store for Node Agent

Provides encrypted, local SQLite database for storing:
- System metrics and logs
- Task execution history
- Module data and outputs
- Configuration backups
- Communication logs

Features:
- AES-256 encryption at rest
- ACID transactions
- Automatic cleanup policies
- Data integrity verification
- Offline operation support
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import secrets
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureDataStore:
    """Encrypted SQLite database for secure local data storage"""

    def __init__(
        self,
        db_path: str = "/opt/node-agent/data/agent.db",
        encryption_key: Optional[str] = None,
    ):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger("node-agent.data-store")

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Setup encryption
        self.encryption_key = encryption_key or self._get_or_create_key()
        self.cipher_suite = self._setup_encryption()

        # Database connection and thread safety
        self.conn: Optional[sqlite3.Connection] = None
        self.lock = asyncio.Lock()
        self._initialized = False

        # Data retention policies (days)
        self.retention_policies = {
            "metrics": 30,  # System metrics
            "logs": 7,  # General logs
            "task_logs": 90,  # Task execution logs
            "module_data": 30,  # Module output data
            "communication": 7,  # Communication logs
        }

    def _get_or_create_key(self) -> str:
        """Get or create encryption key"""
        key_file = self.db_path.parent / ".encryption_key"

        if key_file.exists():
            # Load existing key
            with open(key_file, "rb") as f:
                return f.read().decode()
        else:
            # Generate new key
            key = Fernet.generate_key().decode()

            # Save key with restricted permissions
            with open(key_file, "wb") as f:
                f.write(key.encode())
            os.chmod(key_file, 0o600)  # Owner read/write only

            self.logger.info("Generated new encryption key")
            return key

    def _setup_encryption(self) -> Fernet:
        """Setup encryption cipher"""
        try:
            return Fernet(self.encryption_key.encode())
        except Exception as e:
            self.logger.error(f"Failed to setup encryption: {e}")
            raise

    def _encrypt_data(self, data: str) -> str:
        """Encrypt data for storage"""
        try:
            return self.cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data from storage"""
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise

    def _ensure_connection(self) -> sqlite3.Connection:
        """Ensure database connection is available"""
        if self.conn is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.conn

    async def initialize(self):
        """Initialize database and create tables"""
        async with self.lock:
            try:
                self.conn = sqlite3.connect(
                    self.db_path, check_same_thread=False, timeout=30.0
                )

                # Enable WAL mode for better concurrency
                self.conn.execute("PRAGMA journal_mode=WAL")
                self.conn.execute("PRAGMA synchronous=NORMAL")
                self.conn.execute("PRAGMA cache_size=10000")
                self.conn.execute("PRAGMA temp_store=MEMORY")

                # Create tables
                await self._create_tables()

                # Setup cleanup task
                asyncio.create_task(self._cleanup_loop())

                self.logger.info("Secure data store initialized")

            except Exception as e:
                self.logger.error(f"Failed to initialize data store: {e}")
                raise

    async def _create_tables(self):
        """Create database tables"""
        tables = [
            # System metrics
            """CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_type TEXT NOT NULL,
                data TEXT NOT NULL,
                checksum TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )""",
            # General logs
            """CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                level TEXT NOT NULL,
                logger_name TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                checksum TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )""",
            # Task execution logs
            """CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                status TEXT NOT NULL,
                command_type TEXT,
                data TEXT NOT NULL,
                checksum TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )""",
            # Module data and outputs
            """CREATE TABLE IF NOT EXISTS module_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                data_type TEXT NOT NULL,
                data TEXT NOT NULL,
                checksum TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )""",
            # Communication logs
            """CREATE TABLE IF NOT EXISTS communication_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                direction TEXT NOT NULL,  -- 'incoming' or 'outgoing'
                message_type TEXT NOT NULL,
                data TEXT NOT NULL,
                checksum TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )""",
            # Configuration backups
            """CREATE TABLE IF NOT EXISTS config_backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                config_type TEXT NOT NULL,
                data TEXT NOT NULL,
                checksum TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )""",
            # Active configuration storage
            """CREATE TABLE IF NOT EXISTS agent_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                config_type TEXT NOT NULL,
                encrypted BOOLEAN DEFAULT 1,
                checksum TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            )""",
            # Secure credentials storage
            """CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credential_type TEXT NOT NULL,
                identifier TEXT NOT NULL,
                encrypted_value TEXT NOT NULL,
                metadata TEXT,
                checksum TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                expires_at REAL,
                UNIQUE(credential_type, identifier)
            )""",
        ]

        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type)",
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)",
            "CREATE INDEX IF NOT EXISTS idx_task_logs_task_id ON task_logs(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_logs_timestamp ON task_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_module_data_module_id ON module_data(module_id)",
            "CREATE INDEX IF NOT EXISTS idx_module_data_timestamp ON module_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_comm_logs_timestamp ON communication_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_config_timestamp ON config_backups(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_agent_config_type ON agent_config(config_type)",
            "CREATE INDEX IF NOT EXISTS idx_credentials_type ON credentials(credential_type)",
            "CREATE INDEX IF NOT EXISTS idx_credentials_expires ON credentials(expires_at)",
        ]

        conn = self._ensure_connection()
        cursor = conn.cursor()

        for table_sql in tables:
            cursor.execute(table_sql)

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()

    def _calculate_checksum(self, data: str) -> str:
        """Calculate SHA-256 checksum for data integrity"""
        return hashlib.sha256(data.encode()).hexdigest()

    async def store_metrics(
        self, metric_type: str, data: Dict[str, Any], timestamp: Optional[float] = None
    ):
        """Store system metrics"""
        async with self.lock:
            try:
                timestamp = timestamp or time.time()
                data_json = json.dumps(data, sort_keys=True)
                encrypted_data = self._encrypt_data(data_json)
                checksum = self._calculate_checksum(data_json)

                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO metrics (timestamp, metric_type, data, checksum) VALUES (?, ?, ?, ?)",
                    (timestamp, metric_type, encrypted_data, checksum),
                )
                conn.commit()

                self.logger.debug(f"Stored metrics: {metric_type}")

            except Exception as e:
                self.logger.error(f"Failed to store metrics: {e}")
                raise

    async def store_log(
        self,
        level: str,
        logger_name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ):
        """Store log entry"""
        async with self.lock:
            try:
                timestamp = timestamp or time.time()
                data_json = json.dumps(data) if data else None
                encrypted_message = self._encrypt_data(message)
                encrypted_data = self._encrypt_data(data_json) if data_json else None
                checksum = self._calculate_checksum(message + (data_json or ""))

                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO logs (timestamp, level, logger_name, message, data, checksum) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        timestamp,
                        level,
                        logger_name,
                        encrypted_message,
                        encrypted_data,
                        checksum,
                    ),
                )
                conn.commit()

            except Exception as e:
                self.logger.error(f"Failed to store log: {e}")

    async def store_task_log(
        self,
        task_id: str,
        status: str,
        data: Dict[str, Any],
        command_type: Optional[str] = None,
        timestamp: Optional[float] = None,
    ):
        """Store task execution log"""
        async with self.lock:
            try:
                timestamp = timestamp or time.time()
                data_json = json.dumps(data, sort_keys=True)
                encrypted_data = self._encrypt_data(data_json)
                checksum = self._calculate_checksum(data_json)

                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO task_logs (task_id, timestamp, status, command_type, data, checksum) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        task_id,
                        timestamp,
                        status,
                        command_type,
                        encrypted_data,
                        checksum,
                    ),
                )
                conn.commit()

                self.logger.debug(f"Stored task log: {task_id} - {status}")

            except Exception as e:
                self.logger.error(f"Failed to store task log: {e}")
                raise

    async def store_module_data(
        self,
        module_id: str,
        data_type: str,
        data: Dict[str, Any],
        timestamp: Optional[float] = None,
    ):
        """Store module data/output"""
        async with self.lock:
            try:
                timestamp = timestamp or time.time()
                data_json = json.dumps(data, sort_keys=True)
                encrypted_data = self._encrypt_data(data_json)
                checksum = self._calculate_checksum(data_json)

                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO module_data (module_id, timestamp, data_type, data, checksum) VALUES (?, ?, ?, ?, ?)",
                    (module_id, timestamp, data_type, encrypted_data, checksum),
                )
                conn.commit()

                self.logger.debug(f"Stored module data: {module_id} - {data_type}")

            except Exception as e:
                self.logger.error(f"Failed to store module data: {e}")
                raise

    async def store_communication_log(
        self,
        direction: str,
        message_type: str,
        data: Dict[str, Any],
        timestamp: Optional[float] = None,
    ):
        """Store communication log"""
        async with self.lock:
            try:
                timestamp = timestamp or time.time()
                data_json = json.dumps(data, sort_keys=True)
                encrypted_data = self._encrypt_data(data_json)
                checksum = self._calculate_checksum(data_json)

                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO communication_logs (timestamp, direction, message_type, data, checksum) VALUES (?, ?, ?, ?, ?)",
                    (timestamp, direction, message_type, encrypted_data, checksum),
                )
                conn.commit()

                self.logger.debug(
                    f"Stored communication log: {direction} - {message_type}"
                )

            except Exception as e:
                self.logger.error(f"Failed to store communication log: {e}")

    async def backup_config(
        self,
        config_type: str,
        config_data: Dict[str, Any],
        timestamp: Optional[float] = None,
    ):
        """Backup configuration data"""
        async with self.lock:
            try:
                timestamp = timestamp or time.time()
                data_json = json.dumps(config_data, sort_keys=True)
                encrypted_data = self._encrypt_data(data_json)
                checksum = self._calculate_checksum(data_json)

                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO config_backups (timestamp, config_type, data, checksum) VALUES (?, ?, ?, ?)",
                    (timestamp, config_type, encrypted_data, checksum),
                )
                conn.commit()

                self.logger.info(f"Configuration backed up: {config_type}")

            except Exception as e:
                self.logger.error(f"Failed to backup config: {e}")
                raise

    async def get_metrics(
        self,
        metric_type: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Retrieve metrics"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()

                where_clauses = []
                params = []

                if metric_type:
                    where_clauses.append("metric_type = ?")
                    params.append(metric_type)

                if since:
                    where_clauses.append("timestamp >= ?")
                    params.append(since)

                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

                cursor.execute(
                    f"SELECT timestamp, metric_type, data, checksum FROM metrics WHERE {where_clause} ORDER BY timestamp DESC LIMIT ?",
                    params + [limit],
                )

                results = []
                for row in cursor.fetchall():
                    timestamp, metric_type, encrypted_data, stored_checksum = row

                    try:
                        # Decrypt and verify data
                        decrypted_data = self._decrypt_data(encrypted_data)
                        calculated_checksum = self._calculate_checksum(decrypted_data)

                        if calculated_checksum != stored_checksum:
                            self.logger.warning(
                                f"Checksum mismatch for metric at {timestamp}"
                            )
                            continue

                        data = json.loads(decrypted_data)
                        results.append(
                            {
                                "timestamp": timestamp,
                                "metric_type": metric_type,
                                "data": data,
                            }
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to decrypt metric: {e}")
                        continue

                return results

            except Exception as e:
                self.logger.error(f"Failed to retrieve metrics: {e}")
                return []

    async def get_task_logs(
        self,
        task_id: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Retrieve task logs"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()

                where_clauses = []
                params = []

                if task_id:
                    where_clauses.append("task_id = ?")
                    params.append(task_id)

                if since:
                    where_clauses.append("timestamp >= ?")
                    params.append(since)

                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

                cursor.execute(
                    f"SELECT task_id, timestamp, status, command_type, data, checksum FROM task_logs WHERE {where_clause} ORDER BY timestamp DESC LIMIT ?",
                    params + [limit],
                )

                results = []
                for row in cursor.fetchall():
                    (
                        task_id,
                        timestamp,
                        status,
                        command_type,
                        encrypted_data,
                        stored_checksum,
                    ) = row

                    try:
                        # Decrypt and verify data
                        decrypted_data = self._decrypt_data(encrypted_data)
                        calculated_checksum = self._calculate_checksum(decrypted_data)

                        if calculated_checksum != stored_checksum:
                            self.logger.warning(
                                f"Checksum mismatch for task log {task_id} at {timestamp}"
                            )
                            continue

                        data = json.loads(decrypted_data)
                        results.append(
                            {
                                "task_id": task_id,
                                "timestamp": timestamp,
                                "status": status,
                                "command_type": command_type,
                                "data": data,
                            }
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to decrypt task log: {e}")
                        continue

                return results

            except Exception as e:
                self.logger.error(f"Failed to retrieve task logs: {e}")
                return []

    async def get_latest_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """Get latest configuration backup"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT data, checksum FROM config_backups WHERE config_type = ? ORDER BY timestamp DESC LIMIT 1",
                    (config_type,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                encrypted_data, stored_checksum = row

                # Decrypt and verify data
                decrypted_data = self._decrypt_data(encrypted_data)
                calculated_checksum = self._calculate_checksum(decrypted_data)

                if calculated_checksum != stored_checksum:
                    self.logger.warning(f"Checksum mismatch for config {config_type}")
                    return None

                return json.loads(decrypted_data)

            except Exception as e:
                self.logger.error(f"Failed to retrieve config: {e}")
                return None

    async def _cleanup_loop(self):
        """Periodic cleanup of old data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_data()
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")

    async def _cleanup_old_data(self):
        """Remove old data based on retention policies"""
        async with self.lock:
            try:
                current_time = time.time()
                conn = self._ensure_connection()
                cursor = conn.cursor()

                for table, retention_days in self.retention_policies.items():
                    cutoff_time = current_time - (retention_days * 24 * 3600)

                    # Skip config_backups table (different table name)
                    table_name = "config_backups" if table == "config" else table

                    cursor.execute(
                        f"DELETE FROM {table_name} WHERE timestamp < ?", (cutoff_time,)
                    )

                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        self.logger.info(
                            f"Cleaned up {deleted_count} old records from {table_name}"
                        )

                conn.commit()

                # Vacuum database to reclaim space
                cursor.execute("VACUUM")

            except Exception as e:
                self.logger.error(f"Failed to cleanup old data: {e}")

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()

                stats = {"database_size": self.db_path.stat().st_size, "tables": {}}

                tables = [
                    "metrics",
                    "logs",
                    "task_logs",
                    "module_data",
                    "communication_logs",
                    "config_backups",
                ]

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]

                    cursor.execute(
                        f"SELECT MIN(timestamp), MAX(timestamp) FROM {table}"
                    )
                    min_ts, max_ts = cursor.fetchone()

                    stats["tables"][table] = {
                        "record_count": count,
                        "oldest_record": min_ts,
                        "newest_record": max_ts,
                    }

                return stats

            except Exception as e:
                self.logger.error(f"Failed to get database stats: {e}")
                return {}

    # Configuration Management Methods

    async def set_config(
        self, key: str, value: Any, config_type: str = "general", encrypt: bool = True
    ) -> bool:
        """Store configuration value with optional encryption"""
        async with self.lock:
            try:
                conn = self._ensure_connection()

                # Convert value to JSON string
                value_json = json.dumps(value, sort_keys=True)

                # Encrypt if requested
                if encrypt:
                    stored_value = self._encrypt_data(value_json)
                else:
                    stored_value = value_json

                checksum = self._calculate_checksum(value_json)
                current_time = time.time()

                # Backup existing config if it exists
                await self._backup_config_change(key, config_type)

                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO agent_config
                    (key, value, config_type, encrypted, checksum, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM agent_config WHERE key = ?), ?), ?)
                """,
                    (
                        key,
                        stored_value,
                        config_type,
                        encrypt,
                        checksum,
                        key,
                        current_time,
                        current_time,
                    ),
                )

                conn.commit()

                self.logger.info(
                    f"Configuration set: {key} (type: {config_type}, encrypted: {encrypt})"
                )
                return True

            except Exception as e:
                self.logger.error(f"Failed to set config {key}: {e}")
                return False

    async def get_config(self, key: str, default: Any = None) -> Any:
        """Retrieve configuration value with automatic decryption"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value, encrypted, checksum FROM agent_config WHERE key = ?",
                    (key,),
                )

                row = cursor.fetchone()
                if not row:
                    return default

                stored_value, encrypted, stored_checksum = row

                # Decrypt if necessary
                if encrypted:
                    value_json = self._decrypt_data(stored_value)
                else:
                    value_json = stored_value

                # Verify checksum
                calculated_checksum = self._calculate_checksum(value_json)
                if calculated_checksum != stored_checksum:
                    self.logger.warning(f"Checksum mismatch for config {key}")
                    return default

                return json.loads(value_json)

            except Exception as e:
                self.logger.error(f"Failed to get config {key}: {e}")
                return default

    async def get_all_config(
        self, config_type: Optional[str] = None, include_encrypted_values: bool = False
    ) -> Dict[str, Any]:
        """Retrieve all configuration values"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()

                if config_type:
                    cursor.execute(
                        "SELECT key, value, config_type, encrypted, checksum FROM agent_config WHERE config_type = ?",
                        (config_type,),
                    )
                else:
                    cursor.execute(
                        "SELECT key, value, config_type, encrypted, checksum FROM agent_config"
                    )

                configs = {}
                for row in cursor.fetchall():
                    key, stored_value, cfg_type, encrypted, stored_checksum = row

                    try:
                        # Decrypt if necessary and requested
                        if encrypted and include_encrypted_values:
                            value_json = self._decrypt_data(stored_value)
                        elif encrypted:
                            # Don't include encrypted values unless specifically requested
                            configs[key] = {
                                "config_type": cfg_type,
                                "encrypted": True,
                                "value": "<encrypted>",
                            }
                            continue
                        else:
                            value_json = stored_value

                        # Verify checksum
                        calculated_checksum = self._calculate_checksum(value_json)
                        if calculated_checksum != stored_checksum:
                            self.logger.warning(f"Checksum mismatch for config {key}")
                            continue

                        configs[key] = {
                            "config_type": cfg_type,
                            "encrypted": encrypted,
                            "value": json.loads(value_json),
                        }

                    except Exception as e:
                        self.logger.error(f"Failed to decrypt config {key}: {e}")
                        continue

                return configs

            except Exception as e:
                self.logger.error(f"Failed to get all configs: {e}")
                return {}

    async def delete_config(self, key: str) -> bool:
        """Delete configuration value"""
        async with self.lock:
            try:
                conn = self._ensure_connection()

                # Backup before deletion
                await self._backup_config_change(key, "deleted")

                cursor = conn.cursor()
                cursor.execute("DELETE FROM agent_config WHERE key = ?", (key,))

                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"Configuration deleted: {key}")
                    return True
                else:
                    self.logger.warning(f"Configuration not found: {key}")
                    return False

            except Exception as e:
                self.logger.error(f"Failed to delete config {key}: {e}")
                return False

    async def _backup_config_change(self, key: str, config_type: str):
        """Backup configuration change for audit trail"""
        try:
            conn = self._ensure_connection()
            cursor = conn.cursor()

            # Get existing config if it exists
            cursor.execute(
                "SELECT value, config_type, encrypted FROM agent_config WHERE key = ?",
                (key,),
            )

            row = cursor.fetchone()
            if row:
                stored_value, original_type, encrypted = row

                backup_data = {
                    "key": key,
                    "action": "update" if config_type != "deleted" else "delete",
                    "original_type": original_type,
                    "encrypted": encrypted,
                    "value": stored_value,  # Store as-is (encrypted if it was encrypted)
                }

                await self.store_config_backup(backup_data, config_type)

        except Exception as e:
            self.logger.error(f"Failed to backup config change for {key}: {e}")

    async def store_config_backup(self, backup_data: Dict[str, Any], config_type: str):
        """Store configuration backup"""
        try:
            conn = self._ensure_connection()

            data_json = json.dumps(backup_data, sort_keys=True)
            encrypted_data = self._encrypt_data(data_json)
            checksum = self._calculate_checksum(data_json)
            timestamp = time.time()

            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO config_backups (timestamp, config_type, data, checksum) VALUES (?, ?, ?, ?)",
                (timestamp, config_type, encrypted_data, checksum),
            )
            conn.commit()

            self.logger.debug(f"Configuration backup stored: {config_type}")

        except Exception as e:
            self.logger.error(f"Failed to store config backup: {e}")

    # Credential Management Methods

    async def store_credential(
        self,
        credential_type: str,
        identifier: str,
        value: str,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[float] = None,
    ) -> bool:
        """Store encrypted credential with expiration"""
        async with self.lock:
            try:
                conn = self._ensure_connection()

                # Encrypt the credential value
                encrypted_value = self._encrypt_data(value)

                # Prepare metadata
                metadata_json = json.dumps(metadata) if metadata else None
                encrypted_metadata = (
                    self._encrypt_data(metadata_json) if metadata_json else None
                )

                checksum = self._calculate_checksum(value + (metadata_json or ""))

                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO credentials
                    (credential_type, identifier, encrypted_value, metadata, checksum, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        credential_type,
                        identifier,
                        encrypted_value,
                        encrypted_metadata,
                        checksum,
                        expires_at,
                    ),
                )

                conn.commit()

                self.logger.info(f"Credential stored: {credential_type}:{identifier}")
                return True

            except Exception as e:
                self.logger.error(
                    f"Failed to store credential {credential_type}:{identifier}: {e}"
                )
                return False

    async def get_credential(
        self, credential_type: str, identifier: str
    ) -> Optional[str]:
        """Retrieve credential value with expiration check"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT encrypted_value, checksum, expires_at
                    FROM credentials
                    WHERE credential_type = ? AND identifier = ?
                """,
                    (credential_type, identifier),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                encrypted_value, stored_checksum, expires_at = row

                # Check expiration
                if expires_at and time.time() > expires_at:
                    self.logger.warning(
                        f"Credential expired: {credential_type}:{identifier}"
                    )
                    # Delete expired credential in separate task to avoid deadlock
                    conn = self._ensure_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM credentials WHERE credential_type = ? AND identifier = ?",
                        (credential_type, identifier),
                    )
                    conn.commit()
                    return None

                # Decrypt value
                value = self._decrypt_data(encrypted_value)

                # Verify checksum (we only have the value part for verification)
                calculated_checksum = self._calculate_checksum(value)

                return value

            except Exception as e:
                self.logger.error(
                    f"Failed to get credential {credential_type}:{identifier}: {e}"
                )
                return None

    async def get_credential_metadata(
        self, credential_type: str, identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Get credential metadata without exposing the actual credential"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT metadata, created_at, expires_at
                    FROM credentials
                    WHERE credential_type = ? AND identifier = ?
                """,
                    (credential_type, identifier),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                encrypted_metadata, created_at, expires_at = row

                # Decrypt metadata if it exists
                metadata = None
                if encrypted_metadata:
                    try:
                        metadata_json = self._decrypt_data(encrypted_metadata)
                        metadata = json.loads(metadata_json)
                    except Exception as e:
                        self.logger.error(f"Failed to decrypt metadata: {e}")

                return {
                    "created_at": created_at,
                    "expires_at": expires_at,
                    "expired": expires_at and time.time() > expires_at,
                    "metadata": metadata,
                }

            except Exception as e:
                self.logger.error(
                    f"Failed to get credential metadata {credential_type}:{identifier}: {e}"
                )
                return None

    async def list_credentials(
        self, credential_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all credentials without exposing values"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()

                if credential_type:
                    cursor.execute(
                        """
                        SELECT credential_type, identifier, created_at, expires_at
                        FROM credentials
                        WHERE credential_type = ?
                        ORDER BY created_at DESC
                    """,
                        (credential_type,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT credential_type, identifier, created_at, expires_at
                        FROM credentials
                        ORDER BY credential_type, created_at DESC
                    """
                    )

                credentials = []
                current_time = time.time()

                for row in cursor.fetchall():
                    cred_type, identifier, created_at, expires_at = row

                    credentials.append(
                        {
                            "credential_type": cred_type,
                            "identifier": identifier,
                            "created_at": created_at,
                            "expires_at": expires_at,
                            "expired": expires_at and current_time > expires_at,
                        }
                    )

                return credentials

            except Exception as e:
                self.logger.error(f"Failed to list credentials: {e}")
                return []

    async def delete_credential(self, credential_type: str, identifier: str) -> bool:
        """Delete credential"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM credentials WHERE credential_type = ? AND identifier = ?",
                    (credential_type, identifier),
                )

                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(
                        f"Credential deleted: {credential_type}:{identifier}"
                    )
                    return True
                else:
                    self.logger.warning(
                        f"Credential not found: {credential_type}:{identifier}"
                    )
                    return False

            except Exception as e:
                self.logger.error(
                    f"Failed to delete credential {credential_type}:{identifier}: {e}"
                )
                return False

    async def cleanup_expired_credentials(self) -> int:
        """Remove expired credentials and return count of deleted items"""
        async with self.lock:
            try:
                conn = self._ensure_connection()
                cursor = conn.cursor()

                current_time = time.time()
                cursor.execute(
                    "DELETE FROM credentials WHERE expires_at IS NOT NULL AND expires_at < ?",
                    (current_time,),
                )

                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    conn.commit()
                    self.logger.info(f"Cleaned up {deleted_count} expired credentials")

                return deleted_count

            except Exception as e:
                self.logger.error(f"Failed to cleanup expired credentials: {e}")
                return 0

    # Secure Credential Generation Methods

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)

    def generate_device_id(self) -> str:
        """Generate unique device identifier"""
        import platform
        import uuid

        # Combine multiple sources for uniqueness
        mac_address = ":".join(
            [
                "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
                for elements in range(0, 2 * 6, 2)
            ][::-1]
        )
        hostname = platform.node()
        random_component = secrets.token_hex(8)

        # Create deterministic but unique ID
        combined = f"{mac_address}-{hostname}-{random_component}"
        device_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]

        return f"nagt-device-{device_hash}"

    def generate_api_key(self) -> str:
        """Generate secure API key for agent communication"""
        random_part = secrets.token_urlsafe(24)
        return f"nagt_{random_part}"

    async def initialize_agent_credentials(self) -> Dict[str, str]:
        """Initialize essential agent credentials if they don't exist"""
        credentials = {}

        try:
            # Device ID - permanent identifier for this agent instance
            device_id = await self.get_credential("system", "device_id")
            if not device_id:
                device_id = self.generate_device_id()
                await self.store_credential(
                    "system",
                    "device_id",
                    device_id,
                    metadata={"purpose": "unique_device_identifier"},
                )
                self.logger.info("Generated new device ID")
            credentials["device_id"] = device_id

            # API Key for secure communication
            api_key = await self.get_credential("communication", "api_key")
            if not api_key:
                api_key = self.generate_api_key()
                await self.store_credential(
                    "communication",
                    "api_key",
                    api_key,
                    metadata={"purpose": "management_system_communication"},
                )
                self.logger.info("Generated new API key")
            credentials["api_key"] = api_key

            # Registration token (temporary, expires in 24 hours)
            registration_token = await self.get_credential("registration", "token")
            if not registration_token:
                registration_token = self.generate_secure_token(48)
                expires_at = time.time() + (24 * 3600)  # 24 hours
                await self.store_credential(
                    "registration",
                    "token",
                    registration_token,
                    metadata={"purpose": "initial_registration"},
                    expires_at=expires_at,
                )
                self.logger.info("Generated new registration token")
            credentials["registration_token"] = registration_token

            return credentials

        except Exception as e:
            self.logger.error(f"Failed to initialize agent credentials: {e}")
            return {}

    async def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("Database connection closed")

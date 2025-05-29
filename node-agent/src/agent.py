#!/usr/bin/env python3
"""
Node Agent - Main entry point for AI Stock Trader node agent
Handles management system communication and coordinates all agent activities
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from comms import CommunicationManager
from data_store import SecureDataStore
from module_manager import ModuleManager
from resource_monitor import ResourceMonitor


class NodeAgent:
    """Main node agent class that coordinates all agent activities"""

    def __init__(self, config_dir: str = "/opt/node-agent/config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "agent.json"
        self.device_id_file = self.config_dir / "device_id"

        # Initialize components
        self.config: Dict[str, Any] = {}
        self.device_id: Optional[str] = None
        self.running = False
        self.start_time = time.time()

        # Component managers
        self.comms: Optional[CommunicationManager] = None
        self.resource_monitor: Optional[ResourceMonitor] = None
        self.module_manager: Optional[ModuleManager] = None
        self.data_store: Optional[SecureDataStore] = None

        # Timing for periodic tasks
        self.last_status_time = 0
        self.last_health_log = 0

        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def setup_logging(self):
        """Configure logging for the agent"""
        # Use environment variable for log directory or default to /var/log/node-agent
        log_dir_path = os.environ.get("AGENT_LOG_DIR", "/var/log/node-agent")
        log_dir = Path(log_dir_path)

        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fall back to config directory if we can't write to log directory
            log_dir = self.config_dir / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_dir / "agent.log"),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    async def load_config_from_store(self) -> bool:
        """Load configuration from secure data store"""
        try:
            if not self.data_store:
                return False

            # Get configuration from secure store
            management_url = await self.data_store.get_config("management_url")
            api_key = await self.data_store.get_credential("communication", "api_key")
            device_id = await self.data_store.get_credential("system", "device_id")

            if management_url and api_key and device_id:
                self.config = {
                    "management_url": management_url,
                    "api_key": api_key,
                    "device_id": device_id,
                    "reconnect_interval": await self.data_store.get_config(
                        "reconnect_interval", 30
                    ),
                    "monitoring_interval": await self.data_store.get_config(
                        "monitoring_interval", 60
                    ),
                }
                self.device_id = device_id
                self.logger.info("Configuration loaded from secure store")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to load config from store: {e}")
            return False

    def load_config(self) -> bool:
        """Load agent configuration from file (fallback)"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)

                # Extract device_id and other config from registration data
                self.device_id = self.config.get("device_id")

                self.logger.info("Configuration loaded from file")
                return True
            else:
                self.logger.warning(f"Config file not found: {self.config_file}")
                self.logger.info(
                    "Please run 'python3 register.py' to register this agent"
                )
                return False
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return False

    async def migrate_config_to_store(self):
        """Migrate file-based configuration to secure data store"""
        try:
            if not self.data_store or not self.config:
                return

            # Store configuration values
            if "management_url" in self.config:
                await self.data_store.set_config(
                    "management_url", self.config["management_url"], "system"
                )

            if "api_key" in self.config:
                await self.data_store.store_credential(
                    "communication",
                    "api_key",
                    self.config["api_key"],
                    metadata={"purpose": "management_system_communication"},
                )

            if "device_id" in self.config:
                await self.data_store.store_credential(
                    "system",
                    "device_id",
                    self.config["device_id"],
                    metadata={"purpose": "unique_device_identifier"},
                )

            # Store optional settings
            if "reconnect_interval" in self.config:
                await self.data_store.set_config(
                    "reconnect_interval", self.config["reconnect_interval"], "system"
                )

            if "monitoring_interval" in self.config:
                await self.data_store.set_config(
                    "monitoring_interval", self.config["monitoring_interval"], "system"
                )

            self.logger.info("Configuration migrated to secure store")

        except Exception as e:
            self.logger.error(f"Failed to migrate config to store: {e}")

    def save_config(self):
        """Save current configuration to file (for backward compatibility)"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            self.logger.info("Configuration saved to file")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    def load_or_generate_device_id(self) -> str:
        """Load device ID from secure data store or generate new one"""
        try:
            # Try to get device ID from secure data store first
            if hasattr(self, "data_store") and self.data_store:
                loop = asyncio.get_event_loop()
                device_id = loop.run_until_complete(
                    self.data_store.get_credential("system", "device_id")
                )
                if device_id:
                    self.logger.info(f"Loaded device ID from secure store: {device_id}")
                    return device_id

            # Fallback to file-based storage for backward compatibility
            if self.device_id_file.exists():
                with open(self.device_id_file, "r") as f:
                    device_id = f.read().strip()
                self.logger.info(f"Loaded device ID from file: {device_id}")

                # Migrate to secure storage if available
                if hasattr(self, "data_store") and self.data_store:
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(
                        self.data_store.store_credential(
                            "system",
                            "device_id",
                            device_id,
                            metadata={"purpose": "unique_device_identifier"},
                        )
                    )
                    self.logger.info("Migrated device ID to secure storage")

                return device_id
            else:
                # Generate new device ID using secure method
                if hasattr(self, "data_store") and self.data_store:
                    device_id = self.data_store.generate_device_id()
                else:
                    device_id = str(uuid.uuid4())

                # Save to file for backward compatibility
                self.config_dir.mkdir(parents=True, exist_ok=True)
                with open(self.device_id_file, "w") as f:
                    f.write(device_id)

                self.logger.info(f"Generated new device ID: {device_id}")
                return device_id

        except Exception as e:
            self.logger.error(f"Failed to load/generate device ID: {e}")
            return str(uuid.uuid4())

    def is_registered(self) -> bool:
        """Check if agent is properly registered with management system"""
        return bool(
            self.config.get("device_id")
            and self.config.get("management_url")
            and self.config.get("api_key")
        )

    async def initialize_components(self):
        """Initialize all agent components"""
        try:
            # Initialize secure data store first with configurable path
            db_path = os.environ.get("AGENT_DB_PATH", str(self.config_dir / "agent.db"))
            self.data_store = SecureDataStore(db_path)
            await self.data_store.initialize()

            # Try to load config from secure store first, fallback to file
            config_loaded = await self.load_config_from_store()
            if not config_loaded:
                # Load from file and migrate to store
                if self.load_config():
                    await self.migrate_config_to_store()
                else:
                    raise ValueError(
                        "No configuration found - please register the agent first"
                    )

            # Validate required configuration
            management_url = self.config.get("management_url")
            api_key = self.config.get("api_key")

            if not management_url or not api_key:
                raise ValueError(
                    "Missing required configuration: management_url or api_key"
                )

            # Backup current configuration
            await self.data_store.backup_config("agent_config", self.config)

            # Initialize communication manager
            self.comms = CommunicationManager(
                device_id=self.device_id or "",
                management_url=management_url,
                api_key=api_key,
                reconnect_interval=self.config.get("reconnect_interval", 30),
            )

            # Initialize resource monitor
            self.resource_monitor = ResourceMonitor(
                collection_interval=self.config.get("monitoring_interval", 60)
            )

            # Initialize module manager
            self.module_manager = ModuleManager()

            self.logger.info("All components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            # Store error in data store if available
            if self.data_store:
                await self.data_store.store_log(
                    "ERROR", "agent", f"Component initialization failed: {e}"
                )
            raise

    async def start_components(self):
        """Start all agent components"""
        try:
            # Start data collection
            if self.resource_monitor:
                await self.resource_monitor.start()
                self.logger.info("Resource monitor started")

            # Connect to management system
            if self.comms:
                await self.comms.start()
                self.logger.info("Communication manager started")

            # Log startup to data store
            if self.data_store:
                startup_info = {
                    "start_time": self.start_time,
                    "config": {
                        k: v for k, v in self.config.items() if k != "api_key"
                    },  # Don't log sensitive data
                    "components": {
                        "comms": self.comms is not None,
                        "resource_monitor": self.resource_monitor is not None,
                        "module_manager": self.module_manager is not None,
                        "data_store": self.data_store is not None,
                    },
                }
                await self.data_store.store_log(
                    "INFO", "agent", "Agent startup completed", startup_info
                )

        except Exception as e:
            self.logger.error(f"Failed to start components: {e}")
            if self.data_store:
                await self.data_store.store_log(
                    "ERROR", "agent", f"Component startup failed: {e}"
                )
            raise

    async def stop_components(self):
        """Stop all agent components gracefully"""
        try:
            # Log shutdown
            if self.data_store:
                shutdown_info = {
                    "uptime": time.time() - self.start_time,
                    "reason": "graceful_shutdown",
                }
                await self.data_store.store_log(
                    "INFO", "agent", "Agent shutdown initiated", shutdown_info
                )

            # Stop communication
            if self.comms:
                await self.comms.stop()
                self.logger.info("Communication manager stopped")

            # Stop resource monitoring
            if self.resource_monitor:
                await self.resource_monitor.stop()
                self.logger.info("Resource monitor stopped")

            # Close data store
            if self.data_store:
                await self.data_store.close()
                self.logger.info("Data store closed")

        except Exception as e:
            self.logger.error(f"Error during component shutdown: {e}")

    async def handle_command(self, command: Dict[str, Any]):
        """Handle command from management system"""
        try:
            command_type = command.get("type")
            command_id = command.get("id")

            # Log command receipt
            if self.data_store:
                await self.data_store.store_communication_log(
                    "incoming", command_type or "unknown", command
                )

            self.logger.info(f"Received command: {command_type} (ID: {command_id})")

            result = None

            if command_type == "status":
                # Return current agent status
                result = {
                    "status": "running",
                    "uptime": time.time() - self.start_time,
                    "components": {
                        "comms": self.comms.is_connected() if self.comms else False,
                        "resource_monitor": self.resource_monitor is not None,
                        "module_manager": self.module_manager is not None,
                        "data_store": self.data_store is not None,
                    },
                }

            elif command_type == "run_module":
                # Execute module
                if self.module_manager:
                    module_config = command.get("config", {})
                    module_id = module_config.get("module_id", "unknown")
                    module_args = module_config.get("args", {})
                    result = await self.module_manager.run_module(
                        module_id, module_args
                    )
                else:
                    result = {"error": "Module manager not available"}

            elif command_type == "get_metrics":
                # Collect and return metrics
                if self.resource_monitor:
                    metrics = await self.resource_monitor.get_current_metrics()
                    result = {"metrics": metrics}
                else:
                    result = {"error": "Resource monitor not available"}

            elif command_type == "update_config":
                # Update agent configuration
                new_config = command.get("config", {})
                self.config.update(new_config)

                # Store updated config in secure store
                if self.data_store:
                    for key, value in new_config.items():
                        if key in ["api_key"]:
                            # Store as credential
                            await self.data_store.store_credential(
                                "communication", key, value
                            )
                        else:
                            # Store as config
                            await self.data_store.set_config(key, value, "system")

                result = {"status": "config_updated"}

            else:
                result = {"error": f"Unknown command type: {command_type}"}

            # Send response
            if self.comms and command_id:
                response = {"result": result, "timestamp": time.time()}
                await self.comms.send_response(str(command_id), response)

                # Log response
                if self.data_store:
                    await self.data_store.store_communication_log(
                        "outgoing", "command_response", response
                    )

            # Log command execution
            if self.data_store:
                await self.data_store.store_task_log(
                    command_id or "unknown",
                    "completed",
                    {"command": command, "result": result},
                    command_type,
                )

        except Exception as e:
            self.logger.error(f"Failed to handle command: {e}")

            # Send error response
            command_id = command.get("id")
            if self.comms and command_id:
                error_response = {"error": str(e), "timestamp": time.time()}
                await self.comms.send_response(str(command_id), error_response)

            # Log error
            if self.data_store:
                await self.data_store.store_task_log(
                    command.get("id", "unknown"),
                    "failed",
                    {"command": command, "error": str(e)},
                    command.get("type"),
                )

    async def main_loop(self):
        """Main agent loop"""
        self.logger.info("Starting main agent loop...")

        while self.running:
            try:
                # Check for incoming commands
                if self.comms:
                    commands = await self.comms.get_pending_commands()
                    for command in commands:
                        await self.handle_command(command)

                # Collect and store metrics periodically
                if self.resource_monitor and self.data_store:
                    try:
                        metrics = await self.resource_monitor.get_current_metrics()
                        await self.data_store.store_metrics("system", metrics)
                    except Exception as e:
                        self.logger.error(f"Failed to collect/store metrics: {e}")

                # Send periodic status updates
                if self.comms:
                    current_time = time.time()
                    if current_time - self.last_status_time >= 300:  # Every 5 minutes
                        try:
                            status = {
                                "status": "running",
                                "uptime": current_time - self.start_time,
                                "timestamp": current_time,
                            }

                            await self.comms.send_status_update(status)

                            # Also store communication log
                            if self.data_store:
                                await self.data_store.store_communication_log(
                                    "outgoing", "status_update", status
                                )

                            self.last_status_time = current_time
                        except Exception as e:
                            self.logger.error(f"Failed to send status update: {e}")

                            # Store error for offline analysis
                            if self.data_store:
                                await self.data_store.store_log(
                                    "ERROR", "agent", f"Status update failed: {e}"
                                )

                # Periodic logging of agent health
                current_time = time.time()
                if current_time - self.last_health_log >= 3600:  # Every hour
                    if self.data_store:
                        health_info = {
                            "uptime": current_time - self.start_time,
                            "components_status": {
                                "comms": (
                                    self.comms.is_connected() if self.comms else False
                                ),
                                "resource_monitor": self.resource_monitor is not None,
                                "module_manager": self.module_manager is not None,
                                "data_store": self.data_store is not None,
                            },
                            "running_modules": (
                                len(self.module_manager.running_modules)
                                if self.module_manager
                                else 0
                            ),
                        }

                        await self.data_store.store_log(
                            "INFO", "agent", "Periodic health check", health_info
                        )
                        self.last_health_log = current_time

                # Sleep for a short interval
                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")

                # Store critical errors
                if self.data_store:
                    try:
                        await self.data_store.store_log(
                            "CRITICAL", "agent", f"Main loop error: {e}"
                        )
                    except:
                        pass  # Don't let logging errors crash the main loop

                await asyncio.sleep(5)  # Wait longer on errors

    async def run(self):
        """Main run method"""
        try:
            self.logger.info("Starting Node Agent...")

            # Initialize components (includes config loading)
            await self.initialize_components()

            # Load device ID after data store is available
            self.device_id = self.load_or_generate_device_id()

            # Check if agent is registered
            if not self.is_registered():
                self.logger.error(
                    "Agent is not registered. Please run register.py first."
                )
                return 1

            # Start components
            await self.start_components()

            self.running = True

            # Run main loop
            self.logger.info("Node Agent started successfully")
            await self.main_loop()

        except Exception as e:
            self.logger.error(f"Fatal error in agent: {e}")
            return 1
        finally:
            self.logger.info("Shutting down Node Agent...")
            await self.stop_components()
            self.logger.info("Node Agent shutdown complete")

        return 0


async def main():
    """Entry point for the agent"""
    agent = NodeAgent()
    return await agent.run()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

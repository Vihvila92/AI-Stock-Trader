"""
Communication Manager - Handles all communication with the management system
Supports WebSocket connections, HTTP API calls, and message queuing
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
import websockets
from websockets import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, InvalidURI


class CommunicationManager:
    """Manages communication between agent and management system"""

    def __init__(
        self,
        device_id: str,
        management_url: str,
        api_key: str,
        reconnect_interval: int = 30,
    ):
        self.device_id = device_id
        self.management_url = management_url.rstrip("/")
        self.api_key = api_key
        self.reconnect_interval = reconnect_interval

        # WebSocket connection
        self.websocket: Optional[Any] = None
        self.ws_url = self._build_websocket_url()

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None

        # Connection state
        self.connected = False
        self.reconnecting = False
        self.running = False

        # Message handling
        self.pending_commands: List[Dict[str, Any]] = []
        self.command_responses: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: Dict[str, Callable] = {}

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def _build_websocket_url(self) -> str:
        """Build WebSocket URL from management URL"""
        parsed = urlparse(self.management_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return f"{scheme}://{parsed.netloc}/api/v1/agent/ws/{self.device_id}"

    def _build_api_url(self, endpoint: str) -> str:
        """Build API URL for HTTP requests"""
        return urljoin(self.management_url, f"/api/v1/agent/{endpoint}")

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for HTTP requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"NodeAgent/{self.device_id}",
        }

    async def start(self):
        """Start the communication manager"""
        self.logger.info("Starting communication manager...")
        self.running = True

        # Create HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30), headers=self._get_auth_headers()
        )

        # Start WebSocket connection in background
        asyncio.create_task(self._websocket_manager())

        self.logger.info("Communication manager started")

    async def stop(self):
        """Stop the communication manager"""
        self.logger.info("Stopping communication manager...")
        self.running = False

        # Close WebSocket connection
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        # Close HTTP session
        if self.session:
            await self.session.close()
            self.session = None

        self.connected = False
        self.logger.info("Communication manager stopped")

    def is_connected(self) -> bool:
        """Check if agent is connected to management system"""
        return self.connected and self.websocket is not None

    async def _websocket_manager(self):
        """Manage WebSocket connection with automatic reconnection"""
        while self.running:
            try:
                if not self.connected and not self.reconnecting:
                    await self._connect_websocket()

                if self.connected and self.websocket:
                    try:
                        # Listen for messages
                        async for message in self.websocket:
                            await self._handle_websocket_message(message)
                    except ConnectionClosed:
                        self.logger.warning("WebSocket connection closed")
                        self.connected = False
                        self.websocket = None

            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                self.connected = False
                self.websocket = None

            if not self.connected and self.running:
                self.logger.info(
                    f"Reconnecting in {self.reconnect_interval} seconds..."
                )
                await asyncio.sleep(self.reconnect_interval)

    async def _connect_websocket(self):
        """Establish WebSocket connection"""
        try:
            self.reconnecting = True
            self.logger.info(f"Connecting to WebSocket: {self.ws_url}")

            extra_headers = self._get_auth_headers()
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers=extra_headers,
                ping_interval=30,
                ping_timeout=10,
            )

            self.connected = True
            self.reconnecting = False
            self.logger.info("WebSocket connection established")

            # Send initial connection message
            await self._send_websocket_message(
                {
                    "type": "agent_connected",
                    "device_id": self.device_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to connect WebSocket: {e}")
            self.connected = False
            self.reconnecting = False
            self.websocket = None

    async def _handle_websocket_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            self.logger.debug(f"Received WebSocket message: {msg_type}")

            if msg_type == "command":
                # Add command to pending queue
                self.pending_commands.append(data)

            elif msg_type == "ping":
                # Respond to ping
                await self._send_websocket_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                )

            elif msg_type in self.message_handlers:
                # Call registered handler
                await self.message_handlers[msg_type](data)

            else:
                self.logger.warning(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")

    async def _send_websocket_message(self, data: Dict[str, Any]):
        """Send message via WebSocket"""
        if not self.websocket or not self.connected:
            self.logger.warning("Cannot send WebSocket message: not connected")
            return False

        try:
            message = json.dumps(data)
            await self.websocket.send(message)
            return True
        except Exception as e:
            self.logger.error(f"Failed to send WebSocket message: {e}")
            return False

    async def get_pending_commands(self) -> List[Dict[str, Any]]:
        """Get and clear pending commands from management system"""
        commands = self.pending_commands.copy()
        self.pending_commands.clear()
        return commands

    async def send_response(self, command_id: str, response: Dict[str, Any]):
        """Send response to a command"""
        message = {
            "type": "command_response",
            "command_id": command_id,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Try WebSocket first, fallback to HTTP
        if not await self._send_websocket_message(message):
            await self._send_http_response(command_id, response)

    async def _send_http_response(self, command_id: str, response: Dict[str, Any]):
        """Send command response via HTTP API"""
        if not self.session:
            self.logger.error("Cannot send HTTP response: session not available")
            return

        try:
            url = self._build_api_url(f"commands/{command_id}/response")
            async with self.session.post(url, json=response) as resp:
                if resp.status == 200:
                    self.logger.debug(f"Command response sent via HTTP: {command_id}")
                else:
                    self.logger.error(f"Failed to send HTTP response: {resp.status}")
        except Exception as e:
            self.logger.error(f"Error sending HTTP response: {e}")

    async def send_status_update(self, status: Dict[str, Any]):
        """Send status update to management system"""
        message = {
            "type": "status_update",
            "device_id": self.device_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Try WebSocket first, fallback to HTTP
        if not await self._send_websocket_message(message):
            await self._send_http_status(status)

    async def _send_http_status(self, status: Dict[str, Any]):
        """Send status update via HTTP API"""
        if not self.session:
            self.logger.error("Cannot send HTTP status: session not available")
            return

        try:
            url = self._build_api_url("status")
            async with self.session.post(url, json=status) as resp:
                if resp.status == 200:
                    self.logger.debug("Status update sent via HTTP")
                else:
                    self.logger.error(f"Failed to send HTTP status: {resp.status}")
        except Exception as e:
            self.logger.error(f"Error sending HTTP status: {e}")

    async def send_log_entry(
        self, level: str, message: str, context: Optional[Dict[str, Any]] = None
    ):
        """Send log entry to management system"""
        log_data = {
            "type": "log_entry",
            "device_id": self.device_id,
            "level": level,
            "message": message,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Send via WebSocket (logs are not critical enough for HTTP fallback)
        await self._send_websocket_message(log_data)

    async def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for specific message types"""
        self.message_handlers[message_type] = handler
        self.logger.debug(f"Registered handler for message type: {message_type}")

    async def unregister_message_handler(self, message_type: str):
        """Unregister a message handler"""
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            self.logger.debug(f"Unregistered handler for message type: {message_type}")

    async def send_heartbeat(self):
        """Send heartbeat to management system"""
        heartbeat = {
            "type": "heartbeat",
            "device_id": self.device_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._send_websocket_message(heartbeat)

    async def request_agent_info(self) -> Optional[Dict[str, Any]]:
        """Request agent information from management system"""
        if not self.session:
            return None

        try:
            url = self._build_api_url("info")
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    self.logger.error(f"Failed to get agent info: {resp.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Error requesting agent info: {e}")
            return None

    async def register_device(self, registration_token: str) -> bool:
        """Register this device with the management system using a registration token"""
        import platform

        import psutil

        # Create HTTP session for registration
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                # Generate device ID if not already set
                if not hasattr(self, "device_id") or not self.device_id:
                    self.device_id = str(uuid.uuid4())

                # Collect system information for registration
                system_info = {
                    "platform": {
                        "system": platform.system(),
                        "node": platform.node(),
                        "release": platform.release(),
                        "version": platform.version(),
                        "machine": platform.machine(),
                        "processor": platform.processor(),
                    },
                    "resources": {
                        "cpu_count": psutil.cpu_count(),
                        "memory_total": psutil.virtual_memory().total,
                        "disk_total": sum(
                            [
                                psutil.disk_usage(partition.mountpoint).total
                                for partition in psutil.disk_partitions()
                                if partition.fstype
                            ]
                        ),
                    },
                }

                # Registration payload
                registration_data = {
                    "device_id": self.device_id,
                    "registration_token": registration_token,
                    "system_info": system_info,
                    "agent_version": "1.0.0",
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Send registration request
                url = f"{self.management_url}/api/v1/agent/register"
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": f"NodeAgent/{self.device_id}",
                }

                self.logger.info(f"Sending registration request to {url}")
                async with session.post(
                    url, json=registration_data, headers=headers
                ) as resp:
                    if resp.status == 200:
                        response_data = await resp.json()

                        # Extract API key and management URL from response
                        self.api_key = response_data.get("api_key")
                        if response_data.get("management_url"):
                            self.management_url = response_data[
                                "management_url"
                            ].rstrip("/")

                        # Save configuration
                        await self._save_registration_config(response_data)

                        self.logger.info("Device registration successful")
                        return True
                    elif resp.status == 400:
                        error_msg = await resp.text()
                        self.logger.error(
                            f"Registration failed - invalid token or data: {error_msg}"
                        )
                        return False
                    elif resp.status == 409:
                        self.logger.error(
                            "Registration failed - device already registered"
                        )
                        return False
                    else:
                        error_msg = await resp.text()
                        self.logger.error(
                            f"Registration failed with status {resp.status}: {error_msg}"
                        )
                        return False

            except Exception as e:
                self.logger.error(f"Registration error: {e}")
                return False

    async def _save_registration_config(self, registration_response: Dict[str, Any]):
        """Save registration configuration to file"""
        import os
        from pathlib import Path

        config_dir = Path("/opt/node-agent/config")
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "agent.json"

        config_data = {
            "device_id": self.device_id,
            "api_key": self.api_key,
            "management_url": self.management_url,
            "registered_at": datetime.utcnow().isoformat(),
            "registration_response": registration_response,
        }

        # Write config file
        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2)

        # Set proper permissions (readable only by owner)
        os.chmod(config_file, 0o600)

        self.logger.info(f"Configuration saved to {config_file}")

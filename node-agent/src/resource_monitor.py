"""
Resource Monitor Module

Monitors system resources (CPU, memory, disk, network) and provides
data to the management system.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict

import psutil


class ResourceMonitor:
    """Monitor system resources and collect metrics."""

    def __init__(self, collection_interval: int = 30):
        self.logger = logging.getLogger("node-agent.resource-monitor")
        self.collection_interval = collection_interval
        self.running = False
        self._task = None

    async def start(self):
        """Start resource monitoring."""
        self.logger.info("Starting resource monitoring...")
        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop resource monitoring."""
        self.logger.info("Stopping resource monitoring...")
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                metrics = await self.get_current_metrics()
                self.logger.debug(f"Collected metrics: {metrics}")
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk metrics
            disk_usage = {}
            disk_io = psutil.disk_io_counters()
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": (usage.used / usage.total) * 100,
                    }
                except PermissionError:
                    # Skip partitions we can't access
                    continue

            # Network metrics
            network_io = psutil.net_io_counters()

            # Network connections - may require elevated permissions
            try:
                network_connections = len(psutil.net_connections())
            except (psutil.AccessDenied, PermissionError):
                network_connections = 0  # Fallback when no permission

            # System info
            boot_time = psutil.boot_time()
            load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else None

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": (
                        {
                            "current": cpu_freq.current if cpu_freq else None,
                            "min": cpu_freq.min if cpu_freq else None,
                            "max": cpu_freq.max if cpu_freq else None,
                        }
                        if cpu_freq
                        else None
                    ),
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent,
                    "swap": {
                        "total": swap.total,
                        "used": swap.used,
                        "free": swap.free,
                        "percent": swap.percent,
                    },
                },
                "disk": {
                    "usage": disk_usage,
                    "io": (
                        {
                            "read_count": disk_io.read_count if disk_io else 0,
                            "write_count": disk_io.write_count if disk_io else 0,
                            "read_bytes": disk_io.read_bytes if disk_io else 0,
                            "write_bytes": disk_io.write_bytes if disk_io else 0,
                        }
                        if disk_io
                        else None
                    ),
                },
                "network": {
                    "io": (
                        {
                            "bytes_sent": network_io.bytes_sent if network_io else 0,
                            "bytes_recv": network_io.bytes_recv if network_io else 0,
                            "packets_sent": (
                                network_io.packets_sent if network_io else 0
                            ),
                            "packets_recv": (
                                network_io.packets_recv if network_io else 0
                            ),
                        }
                        if network_io
                        else None
                    ),
                    "connections": network_connections,
                },
                "system": {
                    "boot_time": boot_time,
                    "load_average": load_avg,
                    "uptime": time.time() - boot_time,
                },
            }

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return {"timestamp": datetime.utcnow().isoformat(), "error": str(e)}

    async def get_system_info(self) -> Dict[str, Any]:
        """Get static system information."""
        try:
            import platform

            return {
                "platform": {
                    "system": platform.system(),
                    "node": platform.node(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                },
                "python": {
                    "version": platform.python_version(),
                    "implementation": platform.python_implementation(),
                },
            }
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}

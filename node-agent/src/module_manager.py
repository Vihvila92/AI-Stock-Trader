"""
Module Manager

Handles downloading, installing, and executing modules from the management system.
Supports Python scripts, Node.js applications, shell scripts, and Docker containers.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp


class ModuleManager:
    """Manages module execution and lifecycle."""

    def __init__(self, modules_dir=None, temp_dir=None):
        self.logger = logging.getLogger("node-agent.module-manager")
        self.modules_dir = Path(modules_dir or "/opt/node-agent/modules")
        self.temp_dir = Path(temp_dir or "/tmp/node-agent")
        self.running_modules = {}

        # Ensure directories exist (only if we have permissions)
        try:
            self.modules_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            self.logger.warning(
                f"Cannot create directories - will use existing or fail gracefully"
            )

    async def initialize(self):
        """Initialize the module manager."""
        self.logger.info("Initializing module manager...")

        # Check if Docker is available
        self.docker_available = await self._check_docker()
        if self.docker_available:
            self.logger.info("Docker is available")
        else:
            self.logger.warning(
                "Docker is not available - Docker modules will not work"
            )

        # Check if Node.js is available
        self.nodejs_available = await self._check_nodejs()
        if self.nodejs_available:
            self.logger.info("Node.js is available")
        else:
            self.logger.warning(
                "Node.js is not available - Node.js modules will not work"
            )

    async def cleanup(self):
        """Cleanup running modules and resources."""
        self.logger.info("Cleaning up module manager...")

        # Stop all running modules
        for module_id in list(self.running_modules.keys()):
            await self.stop_module(module_id)

        # Clean temp directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    async def download_module(
        self, module_id: str, download_url: str
    ) -> Optional[Path]:
        """Download a module from the management system."""
        try:
            self.logger.info(f"Downloading module {module_id} from {download_url}")

            module_path = self.modules_dir / module_id
            module_path.mkdir(exist_ok=True)

            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        # Save module archive
                        archive_path = module_path / "module.tar.gz"
                        with open(archive_path, "wb") as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)

                        # Extract archive
                        await self._extract_module(archive_path, module_path)
                        archive_path.unlink()  # Remove archive after extraction

                        self.logger.info(f"Module {module_id} downloaded and extracted")
                        return module_path
                    else:
                        self.logger.error(
                            f"Failed to download module: {response.status}"
                        )
                        return None

        except Exception as e:
            self.logger.error(f"Error downloading module {module_id}: {e}")
            return None

    async def _extract_module(self, archive_path: Path, extract_path: Path):
        """Extract a module archive."""
        import tarfile

        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(extract_path)

    async def run_module(self, module_id: str, args: Dict[str, Any]) -> bool:
        """Run a module with given arguments."""
        try:
            module_path = self.modules_dir / module_id

            if not module_path.exists():
                # Try to download module if not present
                download_url = args.get("download_url")
                if download_url:
                    module_path = await self.download_module(module_id, download_url)
                    if not module_path:
                        return False
                else:
                    self.logger.error(
                        f"Module {module_id} not found and no download URL provided"
                    )
                    return False

            # Read module manifest
            manifest_path = module_path / "manifest.json"
            if not manifest_path.exists():
                self.logger.error(f"Module {module_id} missing manifest.json")
                return False

            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            module_type = manifest.get("type", "python")

            if module_type == "python":
                return await self._run_python_module(
                    module_id, module_path, manifest, args
                )
            elif module_type == "nodejs":
                return await self._run_nodejs_module(
                    module_id, module_path, manifest, args
                )
            elif module_type == "shell":
                return await self._run_shell_module(
                    module_id, module_path, manifest, args
                )
            elif module_type == "docker":
                return await self._run_docker_module(
                    module_id, module_path, manifest, args
                )
            else:
                self.logger.error(f"Unknown module type: {module_type}")
                return False

        except Exception as e:
            self.logger.error(f"Error running module {module_id}: {e}")
            return False

    async def _run_python_module(
        self, module_id: str, module_path: Path, manifest: Dict, args: Dict
    ) -> bool:
        """Run a Python module."""
        entry_point = manifest.get("entry_point", "main.py")
        script_path = module_path / entry_point

        if not script_path.exists():
            self.logger.error(
                f"Python script {entry_point} not found in module {module_id}"
            )
            return False

        # Create environment
        env = os.environ.copy()
        env.update(args.get("env", {}))

        # Run in background if specified
        if manifest.get("background", False):
            process = await asyncio.create_subprocess_exec(
                "python3",
                str(script_path),
                cwd=str(module_path),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self.running_modules[module_id] = {
                "process": process,
                "type": "python",
                "started_at": asyncio.get_event_loop().time(),
            }
            self.logger.info(
                f"Started Python module {module_id} in background (PID: {process.pid})"
            )
            return True
        else:
            # Run and wait for completion
            process = await asyncio.create_subprocess_exec(
                "python3",
                str(script_path),
                cwd=str(module_path),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self.logger.info(f"Python module {module_id} completed successfully")
                return True
            else:
                self.logger.error(
                    f"Python module {module_id} failed with code {process.returncode}"
                )
                self.logger.error(f"stderr: {stderr.decode()}")
                return False

    async def _run_nodejs_module(
        self, module_id: str, module_path: Path, manifest: Dict, args: Dict
    ) -> bool:
        """Run a Node.js module."""
        if not self.nodejs_available:
            self.logger.error("Node.js is not available")
            return False

        entry_point = manifest.get("entry_point", "index.js")
        script_path = module_path / entry_point

        if not script_path.exists():
            self.logger.error(
                f"Node.js script {entry_point} not found in module {module_id}"
            )
            return False

        # Install dependencies if package.json exists
        package_json = module_path / "package.json"
        if package_json.exists():
            install_process = await asyncio.create_subprocess_exec(
                "npm",
                "install",
                cwd=str(module_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await install_process.communicate()

        # Create environment
        env = os.environ.copy()
        env.update(args.get("env", {}))

        # Run the module
        process = await asyncio.create_subprocess_exec(
            "node",
            str(script_path),
            cwd=str(module_path),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if manifest.get("background", False):
            self.running_modules[module_id] = {
                "process": process,
                "type": "nodejs",
                "started_at": asyncio.get_event_loop().time(),
            }
            self.logger.info(
                f"Started Node.js module {module_id} in background (PID: {process.pid})"
            )
            return True
        else:
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                self.logger.info(f"Node.js module {module_id} completed successfully")
                return True
            else:
                self.logger.error(
                    f"Node.js module {module_id} failed with code {process.returncode}"
                )
                return False

    async def _run_shell_module(
        self, module_id: str, module_path: Path, manifest: Dict, args: Dict
    ) -> bool:
        """Run a shell script module."""
        entry_point = manifest.get("entry_point", "run.sh")
        script_path = module_path / entry_point

        if not script_path.exists():
            self.logger.error(
                f"Shell script {entry_point} not found in module {module_id}"
            )
            return False

        # Make script executable
        script_path.chmod(0o755)

        # Create environment
        env = os.environ.copy()
        env.update(args.get("env", {}))

        # Run the script
        process = await asyncio.create_subprocess_exec(
            "bash",
            str(script_path),
            cwd=str(module_path),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if manifest.get("background", False):
            self.running_modules[module_id] = {
                "process": process,
                "type": "shell",
                "started_at": asyncio.get_event_loop().time(),
            }
            self.logger.info(
                f"Started shell module {module_id} in background (PID: {process.pid})"
            )
            return True
        else:
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                self.logger.info(f"Shell module {module_id} completed successfully")
                return True
            else:
                self.logger.error(
                    f"Shell module {module_id} failed with code {process.returncode}"
                )
                return False

    async def _run_docker_module(
        self, module_id: str, module_path: Path, manifest: Dict, args: Dict
    ) -> bool:
        """Run a Docker container module."""
        if not self.docker_available:
            self.logger.error("Docker is not available")
            return False

        image_name = manifest.get("image", f"node-agent-{module_id}")
        dockerfile = module_path / "Dockerfile"

        if dockerfile.exists():
            # Build image
            build_process = await asyncio.create_subprocess_exec(
                "docker",
                "build",
                "-t",
                image_name,
                str(module_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await build_process.communicate()

        # Run container
        docker_args = ["docker", "run"]

        if manifest.get("background", False):
            docker_args.append("-d")
        else:
            docker_args.append("--rm")

        # Add environment variables
        for key, value in args.get("env", {}).items():
            docker_args.extend(["-e", f"{key}={value}"])

        docker_args.append(image_name)

        process = await asyncio.create_subprocess_exec(
            *docker_args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        if manifest.get("background", False):
            stdout, stderr = await process.communicate()
            container_id = stdout.decode().strip()

            self.running_modules[module_id] = {
                "container_id": container_id,
                "type": "docker",
                "started_at": asyncio.get_event_loop().time(),
            }
            self.logger.info(
                f"Started Docker module {module_id} (Container: {container_id})"
            )
            return True
        else:
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                self.logger.info(f"Docker module {module_id} completed successfully")
                return True
            else:
                self.logger.error(
                    f"Docker module {module_id} failed with code {process.returncode}"
                )
                return False

    async def stop_module(self, module_id: str) -> bool:
        """Stop a running module."""
        if module_id not in self.running_modules:
            self.logger.warning(f"Module {module_id} is not running")
            return False

        module_info = self.running_modules[module_id]

        try:
            if module_info["type"] == "docker":
                # Stop Docker container
                process = await asyncio.create_subprocess_exec(
                    "docker",
                    "stop",
                    module_info["container_id"],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()
            else:
                # Terminate process
                process = module_info["process"]
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

            del self.running_modules[module_id]
            self.logger.info(f"Stopped module {module_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping module {module_id}: {e}")
            return False

    async def run_system_command(self, command: str) -> bool:
        """Run a system command (with security restrictions)."""
        # Whitelist of allowed commands for security
        allowed_commands = [
            "apt",
            "yum",
            "brew",
            "systemctl",
            "service",
            "docker",
            "pip",
            "npm",
            "git",
        ]

        command_parts = command.split()
        if not command_parts or command_parts[0] not in allowed_commands:
            self.logger.error(f"Command not allowed: {command}")
            return False

        try:
            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self.logger.info(f"System command completed: {command}")
                return True
            else:
                self.logger.error(f"System command failed: {command}")
                self.logger.error(f"stderr: {stderr.decode()}")
                return False

        except Exception as e:
            self.logger.error(f"Error running system command: {e}")
            return False

    async def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return process.returncode == 0
        except FileNotFoundError:
            return False

    async def _check_nodejs(self) -> bool:
        """Check if Node.js is available."""
        try:
            process = await asyncio.create_subprocess_exec(
                "node",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return process.returncode == 0
        except FileNotFoundError:
            return False

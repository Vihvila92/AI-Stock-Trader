#!/usr/bin/env python3
"""
Node-Agent Registration Tool

This script handles the initial registration of the node-agent with the management system.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from comms import CommunicationManager


async def register_agent():
    """Register the agent with the management system."""
    print("Node-Agent Registration")
    print("=" * 30)

    # Get registration token from user
    print("\nPlease enter the registration token provided by the management system:")
    print("(Token is valid for 30 minutes and is in encoded format)")

    token = input("Registration token: ").strip()

    if not token:
        print("Error: No token provided")
        return False

    # Initialize communication manager
    comm_manager = CommunicationManager()

    print("\nAttempting to register with management system...")

    # Attempt registration
    success = await comm_manager.register_device(token)

    if success:
        print("✓ Registration successful!")
        print(f"✓ Device ID: {comm_manager.device_id}")
        print("✓ Configuration saved")
        print(
            "\nThe agent can now be started and will automatically connect to the management system."
        )
        return True
    else:
        print("✗ Registration failed!")
        print("Please check the token and try again.")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(register_agent())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nRegistration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Registration error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test Agent Integration with Secure Configuration

This script tests that the new agent can properly initialize and use
the secure configuration system.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import NodeAgent
from data_store import SecureDataStore


async def test_agent_with_secure_config():
    """Test agent initialization with secure configuration"""
    print("=== Testing Agent with Secure Configuration ===\n")

    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "agent-config"
        config_dir.mkdir(exist_ok=True)

        print(f"Using test config directory: {config_dir}")

        # Step 1: Setup secure data store with test credentials
        print("\n1. Setting up secure data store...")
        data_store = SecureDataStore(str(config_dir / "agent.db"))
        await data_store.initialize()

        # Initialize agent credentials
        await data_store.initialize_agent_credentials()
        print("✓ Agent credentials initialized")

        # Set required configuration
        await data_store.set_config("management_url", "https://test.example.com/api")
        await data_store.set_config("reconnect_interval", "30")
        await data_store.set_config("monitoring_interval", "60")
        print("✓ Configuration values set")

        await data_store.close()

        # Step 2: Test agent initialization
        print("\n2. Testing agent initialization...")

        # Set environment variables for testing
        os.environ["AGENT_LOG_DIR"] = str(config_dir / "logs")
        os.environ["AGENT_DB_PATH"] = str(config_dir / "agent.db")

        agent = NodeAgent(config_dir=str(config_dir))

        try:
            # Initialize components (this should work with secure config)
            await agent.initialize_components()
            print("✓ Agent components initialized successfully")

            # Verify configuration was loaded
            print(f"✓ Management URL: {agent.config.get('management_url')}")
            print(f"✓ Device ID: {agent.device_id}")
            print(
                f"✓ API Key: {'***' + agent.config.get('api_key', '')[-8:] if agent.config.get('api_key') else 'Not found'}"
            )

            # Test configuration retrieval
            test_value = await agent.data_store.get_config("management_url")
            print(f"✓ Configuration retrieval test: {test_value}")

            print("\n✅ All tests passed!")
            return True

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return False

        finally:
            # Cleanup
            if hasattr(agent, "data_store") and agent.data_store:
                await agent.data_store.close()


async def main():
    """Main test function"""
    try:
        success = await test_agent_with_secure_config()
        return 0 if success else 1

    except Exception as e:
        print(f"Test suite failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

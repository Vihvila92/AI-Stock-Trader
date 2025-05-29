#!/usr/bin/env python3
"""
Test script for secure credential and configuration management
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_store import SecureDataStore


async def test_configuration_management():
    """Test configuration storage and retrieval"""
    print("=== Testing Configuration Management ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_config.db")
        data_store = SecureDataStore(db_path)

        try:
            await data_store.initialize()

            # Test basic config storage
            success = await data_store.set_config(
                "api_endpoint", "https://api.example.com", "system"
            )
            assert success, "Config storage failed"
            print("✓ Configuration storage successful")

            # Test config retrieval
            value = await data_store.get_config("api_endpoint")
            assert (
                value == "https://api.example.com"
            ), f"Expected 'https://api.example.com', got {value}"
            print("✓ Configuration retrieval successful")

            # Test encrypted config
            success = await data_store.set_config(
                "secret_key",
                "super_secret_123",
                "security",
                encrypt=True,  # pragma: allowlist secret
            )
            assert success, "Encrypted config storage failed"
            print("✓ Encrypted configuration storage successful")

            # Test encrypted config retrieval
            secret = await data_store.get_config("secret_key")
            assert (
                secret == "super_secret_123"  # pragma: allowlist secret
            ), f"Expected 'super_secret_123', got {secret}"  # pragma: allowlist secret
            print("✓ Encrypted configuration retrieval successful")

            # Test all config retrieval
            all_configs = await data_store.get_all_config(include_encrypted_values=True)
            assert "api_endpoint" in all_configs, "Config not found in all configs"
            assert (
                "secret_key" in all_configs
            ), "Encrypted config not found in all configs"
            print("✓ All configuration retrieval successful")

            # Test config deletion
            success = await data_store.delete_config("api_endpoint")
            assert success, "Config deletion failed"

            deleted_value = await data_store.get_config("api_endpoint", "default")
            assert deleted_value == "default", "Config was not deleted"
            print("✓ Configuration deletion successful")

        finally:
            await data_store.close()


async def test_credential_management():
    """Test credential storage and retrieval"""
    print("\n=== Testing Credential Management ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_creds.db")
        data_store = SecureDataStore(db_path)

        try:
            await data_store.initialize()

            # Test credential storage
            success = await data_store.store_credential(
                "api",
                "main_key",
                "abc123xyz",
                metadata={"purpose": "main API access"},
                expires_at=None,
            )
            assert success, "Credential storage failed"
            print("✓ Credential storage successful")

            # Test credential retrieval
            cred_value = await data_store.get_credential("api", "main_key")
            assert cred_value == "abc123xyz", f"Expected 'abc123xyz', got {cred_value}"
            print("✓ Credential retrieval successful")

            # Test credential metadata
            metadata = await data_store.get_credential_metadata("api", "main_key")
            assert metadata is not None, "Metadata not found"
            assert (
                metadata["metadata"]["purpose"] == "main API access"
            ), "Incorrect metadata"
            print("✓ Credential metadata retrieval successful")

            # Test credential listing
            creds = await data_store.list_credentials()
            assert len(creds) == 1, f"Expected 1 credential, found {len(creds)}"
            assert creds[0]["credential_type"] == "api", "Incorrect credential type"
            print("✓ Credential listing successful")

            # Test credential deletion
            success = await data_store.delete_credential("api", "main_key")
            assert success, "Credential deletion failed"

            deleted_cred = await data_store.get_credential("api", "main_key")
            assert deleted_cred is None, "Credential was not deleted"
            print("✓ Credential deletion successful")

        finally:
            await data_store.close()


async def test_secure_generation():
    """Test secure credential generation"""
    print("\n=== Testing Secure Generation ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_gen.db")
        data_store = SecureDataStore(db_path)

        try:
            await data_store.initialize()

            # Test secure token generation
            token1 = data_store.generate_secure_token(32)
            token2 = data_store.generate_secure_token(32)
            assert token1 != token2, "Tokens should be unique"
            assert len(token1) > 30, "Token should be reasonably long"
            print("✓ Secure token generation successful")

            # Test device ID generation
            device_id1 = data_store.generate_device_id()
            device_id2 = data_store.generate_device_id()
            assert device_id1 != device_id2, "Device IDs should be unique"
            assert device_id1.startswith(
                "nagt-device-"
            ), "Device ID should have correct prefix"
            print("✓ Device ID generation successful")

            # Test API key generation
            api_key = data_store.generate_api_key()
            assert api_key.startswith("nagt_"), "API key should have correct prefix"
            assert len(api_key) > 20, "API key should be reasonably long"
            print("✓ API key generation successful")

            # Test agent credential initialization
            creds = await data_store.initialize_agent_credentials()
            assert "device_id" in creds, "Device ID not initialized"
            assert "api_key" in creds, "API key not initialized"
            assert "registration_token" in creds, "Registration token not initialized"
            print("✓ Agent credentials initialization successful")

            # Verify credentials were stored
            stored_device_id = await data_store.get_credential("system", "device_id")
            assert (
                stored_device_id == creds["device_id"]
            ), "Device ID not stored correctly"
            print("✓ Credential storage verification successful")

        finally:
            await data_store.close()


async def test_expiration_handling():
    """Test credential expiration handling"""
    print("\n=== Testing Expiration Handling ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_exp.db")
        data_store = SecureDataStore(db_path)

        try:
            await data_store.initialize()

            import time

            # Store credential that expires in 1 second
            expires_at = time.time() + 1
            success = await data_store.store_credential(
                "temp", "short_lived", "temporary_value", expires_at=expires_at
            )
            assert success, "Temporary credential storage failed"
            print("✓ Temporary credential stored")

            # Verify it exists initially
            value = await data_store.get_credential("temp", "short_lived")
            assert value == "temporary_value", "Temporary credential not found"
            print("✓ Temporary credential retrieved before expiration")

            # Wait for expiration
            await asyncio.sleep(2)

            # Verify it's gone after expiration
            expired_value = await data_store.get_credential("temp", "short_lived")
            assert expired_value is None, "Expired credential should be None"
            print("✓ Expired credential handling successful")

            # Test cleanup of expired credentials
            # Add another expired credential
            past_time = time.time() - 3600  # 1 hour ago
            await data_store.store_credential(
                "old", "expired", "old_value", expires_at=past_time
            )

            cleaned_count = await data_store.cleanup_expired_credentials()
            assert cleaned_count >= 0, "Cleanup should return count"
            print(
                f"✓ Expired credentials cleanup successful (cleaned {cleaned_count} items)"
            )

        finally:
            await data_store.close()


async def main():
    """Run all tests"""
    try:
        await test_configuration_management()
        await test_credential_management()
        await test_secure_generation()
        await test_expiration_handling()

        print("\n" + "=" * 50)
        print("🎉 All credential and configuration tests passed!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

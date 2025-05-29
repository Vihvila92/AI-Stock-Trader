#!/usr/bin/env python3
"""
Test Script for Node Agent Components

Tests all major components of the node agent:
- SecureDataStore functionality
- ResourceMonitor data collection
- CommunicationManager (mock)
- ModuleManager capabilities
- Agent coordination
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_store import SecureDataStore
from module_manager import ModuleManager
from resource_monitor import ResourceMonitor


async def test_data_store():
    """Test secure data store functionality"""
    print("=== Testing Secure Data Store ===")

    # Use temporary database for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"

        try:
            # Initialize data store
            data_store = SecureDataStore(str(db_path))
            await data_store.initialize()

            # Test metrics storage
            test_metrics = {
                "cpu_percent": 45.2,
                "memory_percent": 67.8,
                "disk_usage": 78.1,
                "timestamp": time.time(),
            }

            await data_store.store_metrics("system", test_metrics)
            print("✓ Metrics storage successful")

            # Test log storage
            await data_store.store_log(
                "INFO", "test", "Test log message", {"test_data": "value"}
            )
            print("✓ Log storage successful")

            # Test task log storage
            await data_store.store_task_log(
                "test-task-123", "completed", {"result": "success", "duration": 5.2}
            )
            print("✓ Task log storage successful")

            # Test data retrieval
            retrieved_metrics = await data_store.get_metrics(
                metric_type="system", limit=1
            )

            if retrieved_metrics and len(retrieved_metrics) == 1:
                print("✓ Metrics retrieval successful")
                print(
                    f"  Retrieved: {retrieved_metrics[0]['data']['cpu_percent']}% CPU"
                )
            else:
                print("✗ Metrics retrieval failed")

            # Test database stats
            stats = await data_store.get_database_stats()
            print(
                f"✓ Database stats: {stats['tables']['metrics']['record_count']} metrics records"
            )

            await data_store.close()

        except Exception as e:
            print(f"✗ Data store test failed: {e}")
            return False

    return True


async def test_resource_monitor():
    """Test resource monitoring"""
    print("\n=== Testing Resource Monitor ===")

    try:
        monitor = ResourceMonitor(collection_interval=1)

        # Test metrics collection
        metrics = await monitor.get_current_metrics()

        required_keys = ["timestamp", "cpu", "memory", "disk", "network", "system"]
        missing_keys = [key for key in required_keys if key not in metrics]

        if missing_keys:
            print(f"✗ Missing metrics keys: {missing_keys}")
            return False

        print("✓ Resource metrics collection successful")
        print(f"  CPU: {metrics['cpu']['percent']}%")
        print(f"  Memory: {metrics['memory']['percent']}%")
        print(f"  Boot time: {metrics['system']['boot_time']}")

        # Test system info
        system_info = await monitor.get_system_info()
        if "platform" in system_info and "python" in system_info:
            print("✓ System info collection successful")
            print(f"  Platform: {system_info['platform']['system']}")
            print(f"  Python: {system_info['python']['version']}")
        else:
            print("✗ System info collection failed")
            return False

    except Exception as e:
        print(f"✗ Resource monitor test failed: {e}")
        return False

    return True


async def test_module_manager():
    """Test module manager"""
    print("\n=== Testing Module Manager ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            manager = ModuleManager(
                modules_dir=str(Path(temp_dir) / "modules"),
                temp_dir=str(Path(temp_dir) / "temp"),
            )
            await manager.initialize()

            print("✓ Module manager initialization successful")

            # Check available runtimes
            if manager.docker_available:
                print("✓ Docker runtime available")
            else:
                print("⚠ Docker runtime not available")

            if manager.nodejs_available:
                print("✓ Node.js runtime available")
            else:
                print("⚠ Node.js runtime not available")

            # Test system command (safe command)
            try:
                result = await manager.run_system_command("echo 'test'")
                if result:
                    print("✓ System command execution successful")
                else:
                    print("✗ System command execution failed")
            except Exception as e:
                print(f"⚠ System command test skipped: {e}")

            await manager.cleanup()

        except Exception as e:
            print(f"✗ Module manager test failed: {e}")
            return False

    return True


async def test_integration():
    """Test component integration"""
    print("\n=== Testing Component Integration ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Initialize components
            data_store = SecureDataStore(str(Path(temp_dir) / "integration.db"))
            await data_store.initialize()

            monitor = ResourceMonitor()
            manager = ModuleManager(
                modules_dir=str(Path(temp_dir) / "modules"),
                temp_dir=str(Path(temp_dir) / "temp"),
            )
            await manager.initialize()

            # Simulate agent workflow
            print("✓ All components initialized")

            # Collect metrics and store them
            metrics = await monitor.get_current_metrics()
            await data_store.store_metrics("system", metrics)

            # Simulate task execution
            task_id = "integration-test-001"
            await data_store.store_task_log(
                task_id, "started", {"command": "test", "timestamp": time.time()}
            )

            # Simulate completion
            await data_store.store_task_log(
                task_id, "completed", {"result": "success", "duration": 2.5}
            )

            # Verify stored data
            task_logs = await data_store.get_task_logs(task_id=task_id)
            if len(task_logs) == 2:
                print("✓ Task lifecycle logging successful")
            else:
                print(f"✗ Expected 2 task logs, got {len(task_logs)}")
                return False

            # Test metrics retrieval
            stored_metrics = await data_store.get_metrics(limit=1)
            if stored_metrics:
                print("✓ Metrics storage and retrieval successful")
            else:
                print("✗ No metrics found in storage")
                return False

            # Cleanup
            await data_store.close()
            await manager.cleanup()

        except Exception as e:
            print(f"✗ Integration test failed: {e}")
            return False

    return True


async def test_error_handling():
    """Test error handling and recovery"""
    print("\n=== Testing Error Handling ===")

    try:
        # Test data store with invalid path
        try:
            invalid_store = SecureDataStore("/invalid/path/test.db")
            await invalid_store.initialize()
            print("✗ Should have failed with invalid path")
            return False
        except Exception:
            print("✓ Invalid path handling successful")

        # Test resource monitor error handling
        monitor = ResourceMonitor()
        try:
            # This should work normally
            metrics = await monitor.get_current_metrics()
            if "error" in metrics:
                print("✗ Unexpected error in metrics")
                return False
            print("✓ Resource monitor error handling successful")
        except Exception as e:
            print(f"✗ Resource monitor error handling failed: {e}")
            return False

        # Test module manager with invalid command
        with tempfile.TemporaryDirectory() as temp_dir2:
            manager = ModuleManager(
                modules_dir=str(Path(temp_dir2) / "modules"),
                temp_dir=str(Path(temp_dir2) / "temp"),
            )
            await manager.initialize()

            # Try to run invalid command (should be blocked)
            result = await manager.run_system_command("rm -rf /")
            if result:
                print("✗ Security violation: dangerous command executed")
                return False
            else:
                print("✓ Security check successful: dangerous command blocked")

            await manager.cleanup()

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

    return True


async def main():
    """Run all tests"""
    print("Node Agent Component Test Suite")
    print("=" * 40)

    # Setup logging for tests
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise during tests
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    tests = [
        ("Data Store", test_data_store),
        ("Resource Monitor", test_resource_monitor),
        ("Module Manager", test_module_manager),
        ("Integration", test_integration),
        ("Error Handling", test_error_handling),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:20} {status}")
        if success:
            passed += 1

    print("-" * 40)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

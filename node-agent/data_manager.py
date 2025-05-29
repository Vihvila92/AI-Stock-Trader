#!/usr/bin/env python3
"""
Data Store Management CLI

Command-line interface for managing the secure data store:
- View stored data
- Export data
- Cleanup old data
- Database statistics
- Data integrity checks
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import with type ignore to suppress Pylance warnings about relative imports
from data_store import SecureDataStore  # type: ignore[import]


async def show_stats(data_store: SecureDataStore):
    """Show database statistics"""
    stats = await data_store.get_database_stats()

    print("=== Database Statistics ===")
    print(f"Database size: {stats.get('database_size', 0) / 1024 / 1024:.2f} MB")
    print()

    for table, table_stats in stats.get("tables", {}).items():
        print(f"{table.title()} Table:")
        print(f"  Records: {table_stats.get('record_count', 0)}")

        oldest = table_stats.get("oldest_record")
        newest = table_stats.get("newest_record")

        if oldest:
            oldest_dt = datetime.fromtimestamp(oldest)
            print(f"  Oldest: {oldest_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        if newest:
            newest_dt = datetime.fromtimestamp(newest)
            print(f"  Newest: {newest_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        print()


async def export_metrics(
    data_store: SecureDataStore,
    metric_type: str | None = None,
    since_hours: int = 24,
    limit: int = 1000,
):
    """Export metrics to JSON"""
    since = time.time() - (since_hours * 3600)
    metrics = await data_store.get_metrics(metric_type, since, limit)

    print(f"=== Metrics Export ===")
    print(f"Type: {metric_type or 'All'}")
    print(f"Since: {datetime.fromtimestamp(since).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Records: {len(metrics)}")
    print()

    for metric in metrics:
        timestamp = datetime.fromtimestamp(metric["timestamp"])
        print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {metric['metric_type']}")
        print(json.dumps(metric["data"], indent=2))
        print("-" * 50)


async def export_task_logs(
    data_store: SecureDataStore,
    task_id: str | None = None,
    since_hours: int = 24,
    limit: int = 1000,
):
    """Export task logs"""
    since = time.time() - (since_hours * 3600)
    logs = await data_store.get_task_logs(task_id, since, limit)

    print(f"=== Task Logs Export ===")
    print(f"Task ID: {task_id or 'All'}")
    print(f"Since: {datetime.fromtimestamp(since).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Records: {len(logs)}")
    print()

    for log in logs:
        timestamp = datetime.fromtimestamp(log["timestamp"])
        print(
            f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {log['task_id']} - {log['status']}"
        )
        if log.get("command_type"):
            print(f"  Command: {log['command_type']}")
        print(json.dumps(log["data"], indent=2))
        print("-" * 50)


async def export_json(
    data_store: SecureDataStore,
    output_file: str,
    since_hours: int = 24,
    include_types: list | None = None,
):
    """Export all data to JSON file"""
    since = time.time() - (since_hours * 3600)

    export_data = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "since": datetime.fromtimestamp(since).isoformat(),
        "data": {},
    }

    # Export different data types
    types_to_export = include_types or ["metrics", "task_logs"]

    if "metrics" in types_to_export:
        print("Exporting metrics...")
        export_data["data"]["metrics"] = await data_store.get_metrics(
            since=since, limit=10000
        )

    if "task_logs" in types_to_export:
        print("Exporting task logs...")
        export_data["data"]["task_logs"] = await data_store.get_task_logs(
            since=since, limit=10000
        )

    # Write to file
    with open(output_file, "w") as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"Data exported to: {output_file}")


async def cleanup_data(data_store: SecureDataStore, older_than_days: int):
    """Manually trigger data cleanup"""
    print(f"Cleaning up data older than {older_than_days} days...")

    # This would need to be implemented in the data store
    # For now, just show what would be cleaned
    cutoff_time = time.time() - (older_than_days * 24 * 3600)
    cutoff_dt = datetime.fromtimestamp(cutoff_time)

    print(f"Would clean data older than: {cutoff_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Manual cleanup not yet implemented - use automatic cleanup instead")


async def show_configs(
    data_store: SecureDataStore,
    config_type: str | None = None,
    show_encrypted: bool = False,
):
    """Show stored configurations"""
    configs = await data_store.get_all_config(config_type, show_encrypted)

    print("=== Configuration Settings ===")
    if config_type:
        print(f"Type filter: {config_type}")
    print(f"Show encrypted values: {show_encrypted}")
    print()

    if not configs:
        print("No configurations found")
        return

    for key, config in configs.items():
        print(f"Key: {key}")
        print(f"  Type: {config['config_type']}")
        print(f"  Encrypted: {config['encrypted']}")
        print(f"  Value: {config['value']}")
        print()


async def show_credentials(
    data_store: SecureDataStore, credential_type: str | None = None
):
    """Show stored credentials (metadata only)"""
    credentials = await data_store.list_credentials(credential_type)

    print("=== Stored Credentials ===")
    if credential_type:
        print(f"Type filter: {credential_type}")
    print()

    if not credentials:
        print("No credentials found")
        return

    for cred in credentials:
        print(f"Type: {cred['credential_type']}")
        print(f"  Identifier: {cred['identifier']}")
        print(
            f"  Created: {datetime.fromtimestamp(cred['created_at']).strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if cred["expires_at"]:
            expires_dt = datetime.fromtimestamp(cred["expires_at"])
            print(f"  Expires: {expires_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            if cred["expired"]:
                print("  Status: EXPIRED")
            else:
                print("  Status: Valid")
        else:
            print("  Expires: Never")
        print()


async def init_agent_credentials(data_store: SecureDataStore):
    """Initialize agent credentials"""
    print("=== Initializing Agent Credentials ===")

    credentials = await data_store.initialize_agent_credentials()

    print("Generated credentials:")
    for key, value in credentials.items():
        if key == "registration_token":
            # Show only part of sensitive tokens
            display_value = value[:8] + "..." + value[-4:] if len(value) > 12 else value
        else:
            display_value = value
        print(f"  {key}: {display_value}")

    print("\nCredentials have been securely stored in the database.")


async def cleanup_expired(data_store: SecureDataStore):
    """Cleanup expired credentials"""
    print("=== Cleaning Up Expired Credentials ===")

    count = await data_store.cleanup_expired_credentials()
    print(f"Removed {count} expired credentials")


async def set_config_value(
    data_store: SecureDataStore,
    key: str,
    value: str,
    config_type: str = "general",
    encrypt: bool = False,
):
    """Set a configuration value"""
    print(f"=== Setting Configuration ===")
    print(f"Key: {key}")
    print(f"Value: {value}")
    print(f"Type: {config_type}")
    print(f"Encrypted: {encrypt}")

    # Try to parse as JSON if it looks like JSON
    try:
        if value.startswith(("{", "[", '"')) or value in ("true", "false", "null"):
            parsed_value = json.loads(value)
        else:
            # Try to parse as number
            if "." in value:
                parsed_value = float(value)
            else:
                parsed_value = int(value)
    except (json.JSONDecodeError, ValueError):
        # Keep as string
        parsed_value = value

    success = await data_store.set_config(key, parsed_value, config_type, encrypt)

    if success:
        print("✓ Configuration saved successfully")
    else:
        print("✗ Failed to save configuration")


async def verify_integrity(data_store: SecureDataStore):
    """Verify data integrity by checking checksums"""
    print("=== Data Integrity Check ===")
    print("Checking checksums...")

    # This would need to be implemented in the data store
    # For now, just show that it's not implemented
    print("Data integrity verification not yet implemented")
    print("The data store automatically verifies checksums on read operations")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Node Agent Data Store Management")
    parser.add_argument(
        "--db-path",
        default="/opt/node-agent/data/agent.db",
        help="Path to database file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")

    # Export metrics command
    metrics_parser = subparsers.add_parser("export-metrics", help="Export metrics")
    metrics_parser.add_argument("--type", help="Metric type to export")
    metrics_parser.add_argument(
        "--since-hours", type=int, default=24, help="Export data from last N hours"
    )
    metrics_parser.add_argument(
        "--limit", type=int, default=1000, help="Maximum records to export"
    )

    # Export task logs command
    logs_parser = subparsers.add_parser("export-logs", help="Export task logs")
    logs_parser.add_argument("--task-id", help="Specific task ID to export")
    logs_parser.add_argument(
        "--since-hours", type=int, default=24, help="Export data from last N hours"
    )
    logs_parser.add_argument(
        "--limit", type=int, default=1000, help="Maximum records to export"
    )

    # Export JSON command
    json_parser = subparsers.add_parser("export-json", help="Export data to JSON file")
    json_parser.add_argument("output_file", help="Output JSON file path")
    json_parser.add_argument(
        "--since-hours", type=int, default=24, help="Export data from last N hours"
    )
    json_parser.add_argument(
        "--include",
        nargs="+",
        choices=["metrics", "task_logs", "module_data"],
        default=["metrics", "task_logs"],
        help="Data types to include",
    )

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup old data")
    cleanup_parser.add_argument(
        "--older-than-days",
        type=int,
        required=True,
        help="Delete data older than N days",
    )

    # Verify command
    subparsers.add_parser("verify", help="Verify data integrity")

    # Config commands
    config_parser = subparsers.add_parser(
        "show-config", help="Show configuration values"
    )
    config_parser.add_argument("--type", help="Configuration type filter")
    config_parser.add_argument(
        "--show-encrypted",
        action="store_true",
        help="Show encrypted values (use with caution)",
    )

    set_config_parser = subparsers.add_parser(
        "set-config", help="Set configuration value"
    )
    set_config_parser.add_argument("key", help="Configuration key")
    set_config_parser.add_argument("value", help="Configuration value")
    set_config_parser.add_argument(
        "--type", default="general", help="Configuration type"
    )
    set_config_parser.add_argument(
        "--encrypt", action="store_true", help="Encrypt the configuration value"
    )

    # Credential commands
    creds_parser = subparsers.add_parser(
        "show-credentials", help="Show stored credentials"
    )
    creds_parser.add_argument("--type", help="Credential type filter")

    subparsers.add_parser("init-credentials", help="Initialize agent credentials")
    subparsers.add_parser("cleanup-expired", help="Clean up expired credentials")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize data store
    try:
        data_store = SecureDataStore(args.db_path)
        await data_store.initialize()

        # Execute command
        if args.command == "stats":
            await show_stats(data_store)

        elif args.command == "export-metrics":
            await export_metrics(data_store, args.type, args.since_hours, args.limit)

        elif args.command == "export-logs":
            await export_task_logs(
                data_store, args.task_id, args.since_hours, args.limit
            )

        elif args.command == "export-json":
            await export_json(
                data_store, args.output_file, args.since_hours, args.include
            )

        elif args.command == "cleanup":
            await cleanup_data(data_store, args.older_than_days)

        elif args.command == "verify":
            await verify_integrity(data_store)

        elif args.command == "show-config":
            await show_configs(data_store, args.type, args.show_encrypted)

        elif args.command == "set-config":
            await set_config_value(
                data_store, args.key, args.value, args.type, args.encrypt
            )

        elif args.command == "show-credentials":
            await show_credentials(data_store, args.type)

        elif args.command == "init-credentials":
            await init_agent_credentials(data_store)

        elif args.command == "cleanup-expired":
            await cleanup_expired(data_store)

        await data_store.close()
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

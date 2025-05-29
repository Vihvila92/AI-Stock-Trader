# Node Agent

A secure, lightweight agent that runs on individual devices to enable remote management and monitoring as part of the AI Stock Trader system. The agent provides secure communication, resource monitoring, module execution, and comprehensive data storage with encryption.

## Key Features

### 🔐 Security

- **Encrypted Data Storage**: AES-256 encryption at rest with per-device keys
- **Secure Communication**: TLS-encrypted HTTPS and WebSocket connections
- **Command Validation**: Strict command filtering and validation
- **Time-limited Registration**: Registration tokens expire after 30 minutes
- **Access Control**: Restricted file permissions and secure configuration storage

### 📊 Monitoring & Data Collection

- **System Metrics**: CPU, memory, disk, network, and system information
- **Resource Monitoring**: Real-time system resource tracking
- **Activity Logging**: Comprehensive logging of all agent activities
- **Offline Operation**: Continues operation during management system outages
- **Data Integrity**: SHA-256 checksums for all stored data

### 🔧 Module Management

- **Docker Support**: Execute containerized modules
- **Node.js Support**: Run JavaScript modules
- **System Commands**: Controlled execution of system commands
- **Runtime Detection**: Automatic detection of available runtimes
- **Lifecycle Management**: Start, stop, monitor module execution

### 💾 Data Management

- **Persistent Storage**: SQLite database with WAL mode for concurrency
- **Data Retention**: Configurable automatic cleanup policies
- **Export Capabilities**: Export metrics, logs, and data to various formats
- **Database Statistics**: Monitor storage usage and performance
- **Data Recovery**: Verify data integrity and recover from corruption

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Management      │◄──►│ Node Agent      │◄──►│ Local System    │
│ System          │    │                 │    │ Resources       │
└─────────────────┘    │ ┌─────────────┐ │    └─────────────────┘
                       │ │SecureData   │ │
                       │ │Store        │ │
                       │ └─────────────┘ │
                       │ ┌─────────────┐ │
                       │ │Resource     │ │
                       │ │Monitor      │ │
                       │ └─────────────┘ │
                       │ ┌─────────────┐ │
                       │ │Module       │ │
                       │ │Manager      │ │
                       │ └─────────────┘ │
                       │ ┌─────────────┐ │
                       │ │Communication│ │
                       │ │Manager      │ │
                       │ └─────────────┘ │
                       └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Docker (optional, for containerized modules)
- Node.js (optional, for JavaScript modules)

### Supported Platforms

- **Linux**: Ubuntu 18.04+, CentOS 7+, RHEL 7+
- **macOS**: 10.14+ (Mojave)

### Quick Install

```bash
# Clone or download the node-agent directory
cd node-agent

# Run the installation script
sudo ./install.sh

# The installer will:
# - Install Python dependencies
# - Create system directories
# - Set up the systemd service (Linux) or launchd service (macOS)
# - Configure proper permissions
```

### Manual Installation

```bash
# Install dependencies
pip3 install -r requirements.txt

# Create directories
sudo mkdir -p /opt/node-agent/{modules,data,logs}
sudo mkdir -p /etc/node-agent

# Set permissions
sudo chown -R $USER:$USER /opt/node-agent
sudo chmod 750 /opt/node-agent
sudo chmod 700 /opt/node-agent/data

# Copy agent files
sudo cp -r src/* /opt/node-agent/
sudo cp register.py /opt/node-agent/
sudo cp data_manager.py /opt/node-agent/
```

## Configuration

### Initial Registration

Before the agent can communicate with the management system, it must be registered:

```bash
# Get a registration token from the management system
# Then run the registration script
python3 /opt/node-agent/register.py

# Enter the token when prompted
# The agent will automatically configure itself
```

### Manual Configuration

Create `/etc/node-agent/config.json`:

```json
{
  "device_id": "unique-device-identifier",
  "management_url": "https://your-management-system.com",
  "api_key": "your-api-key", # pragma: allowlist secret
  "collection_interval": 60,
  "log_level": "INFO",
  "data_retention_days": 30
}
```

### Environment Variables

You can also configure using environment variables:

```bash
export NODE_AGENT_DEVICE_ID="device-001"
export NODE_AGENT_MANAGEMENT_URL="https://management.example.com"
export NODE_AGENT_API_KEY="your-api-key" # pragma: allowlist secret
export NODE_AGENT_LOG_LEVEL="INFO"
```

## Usage

### Service Management

**Linux (systemd):**

```bash
# Start the agent
sudo systemctl start node-agent

# Enable auto-start
sudo systemctl enable node-agent

# Check status
sudo systemctl status node-agent

# View logs
sudo journalctl -u node-agent -f
```

**macOS (launchd):**

```bash
# Load the service
sudo launchctl load /Library/LaunchDaemons/com.ai-stock-trader.node-agent.plist

# Start the service
sudo launchctl start com.ai-stock-trader.node-agent

# Check status
sudo launchctl list | grep node-agent

# View logs
tail -f /opt/node-agent/logs/agent.log
```

### Data Management

The agent includes a comprehensive data management tool:

```bash
# Show database statistics
python3 /opt/node-agent/data_manager.py stats

# Export metrics to CSV
python3 /opt/node-agent/data_manager.py export-metrics --output metrics.csv

# Export logs
python3 /opt/node-agent/data_manager.py export-logs --output logs.json

# Export all data to JSON
python3 /opt/node-agent/data_manager.py export-json --output backup.json

# Cleanup old data (older than 30 days)
python3 /opt/node-agent/data_manager.py cleanup --days 30

# Verify data integrity
python3 /opt/node-agent/data_manager.py verify
```

### Testing

Run the comprehensive test suite:

```bash
cd node-agent
python3 test_agent.py
```

## Data Storage

### Database Schema

The agent uses SQLite with the following tables:

- **metrics**: System performance data
- **logs**: Application and system logs
- **task_logs**: Task execution history
- **module_data**: Module-specific data
- **communication_logs**: Management system communication
- **config_backups**: Configuration change history

### Encryption

- **At Rest**: AES-256 encryption for all data
- **Keys**: Unique per-device encryption keys
- **Integrity**: SHA-256 checksums for verification
- **Storage**: Encrypted database files with `.enc` extension

### Data Retention

Default retention policies:

- **Metrics**: 30 days
- **Logs**: 30 days
- **Task Logs**: 90 days
- **Communication Logs**: 7 days
- **Config Backups**: No automatic cleanup

## Security

### Data Protection

- All data encrypted at rest using AES-256
- Unique encryption keys per device
- Secure key storage with restricted permissions
- Data integrity verification using checksums

### Communication Security

- TLS 1.2+ for all HTTP communications
- Certificate validation for management system
- API key authentication
- Rate limiting and request validation

### System Security

- Minimal privilege execution
- Command filtering and validation
- Secure temporary file handling
- Log rotation and cleanup

### File Permissions

```
/opt/node-agent/          755 (agent:agent)
/opt/node-agent/data/     700 (agent:agent)
/opt/node-agent/logs/     750 (agent:agent)
/etc/node-agent/          750 (root:agent)
/etc/node-agent/config.json  640 (root:agent)
```

## Troubleshooting

### Common Issues

**Permission Denied Errors:**

```bash
# Fix ownership
sudo chown -R node-agent:node-agent /opt/node-agent

# Fix permissions
sudo chmod 750 /opt/node-agent
sudo chmod 700 /opt/node-agent/data
```

**Service Won't Start:**

```bash
# Check logs
sudo journalctl -u node-agent -n 50

# Verify configuration
python3 -c "import json; print(json.load(open('/etc/node-agent/config.json')))"

# Test connectivity
curl -k https://your-management-system.com/health
```

**High Memory Usage:**

```bash
# Check database size
python3 /opt/node-agent/data_manager.py stats

# Cleanup old data
python3 /opt/node-agent/data_manager.py cleanup --days 7
```

### Log Locations

- **System logs**: `/var/log/node-agent/`
- **Application logs**: `/opt/node-agent/logs/`
- **systemd logs**: `journalctl -u node-agent`
- **macOS logs**: `/opt/node-agent/logs/agent.log`

### Debug Mode

Enable debug logging:

```bash
# Edit config.json
"log_level": "DEBUG"

# Or use environment variable
export NODE_AGENT_LOG_LEVEL="DEBUG"

# Restart service
sudo systemctl restart node-agent
```

## API Reference

### Internal APIs

The agent exposes internal APIs for module communication:

**Health Check:**

```python
GET /health
Response: {"status": "healthy", "uptime": 12345}
```

**Metrics:**

```python
GET /metrics
Response: {"cpu": 45.2, "memory": 67.8, ...}
```

**System Info:**

```python
GET /system
Response: {"platform": "Linux", "version": "5.4.0", ...}
```

## Development

### Running Tests

```bash
# Install development dependencies
pip3 install -r requirements.txt

# Run all tests
python3 test_agent.py

# Run specific component tests
python3 -c "
import asyncio
from test_agent import test_data_store
asyncio.run(test_data_store())
"
```

### Code Structure

```
src/
├── agent.py              # Main agent coordinator
├── comms.py             # Communication with management system
├── data_store.py        # Secure data storage
├── module_manager.py    # Module execution and lifecycle
└── resource_monitor.py  # System resource monitoring
```

### Contributing

1. Follow PEP 8 style guidelines
2. Add comprehensive error handling
3. Include tests for new features
4. Update documentation
5. Ensure security best practices

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and issues:

1. Check the troubleshooting section above
2. Review logs for error messages
3. Verify network connectivity to management system
4. Ensure proper permissions and configuration

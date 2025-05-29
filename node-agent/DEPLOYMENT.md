# Node Agent Production Deployment Checklist

## Pre-Deployment Validation

### ✅ System Requirements

- [ ] Python 3.8+ installed
- [ ] pip package manager available
- [ ] Sufficient disk space (minimum 1GB for agent + data)
- [ ] Network connectivity to management system
- [ ] Appropriate user permissions for installation

### ✅ Dependencies

- [ ] All Python packages in requirements.txt installed
- [ ] Optional: Docker installed and running (for containerized modules)
- [ ] Optional: Node.js installed (for JavaScript modules)

### ✅ Security Checklist

- [ ] TLS certificates valid for management system
- [ ] Registration token obtained from management system
- [ ] Firewall rules configured for outbound HTTPS/WSS
- [ ] User account created for agent (non-root)
- [ ] File permissions configured correctly

## Installation Validation

### ✅ Quick Test

```bash
# Run the test suite
cd node-agent
python3 test_agent.py

# Expected: All 5 tests should pass
# ✓ Data Store           PASS
# ✓ Resource Monitor     PASS
# ✓ Module Manager       PASS
# ✓ Integration          PASS
# ✓ Error Handling       PASS
```

### ✅ Installation Steps

```bash
# 1. Extract/clone the node-agent directory
cd node-agent

# 2. Run installation script
sudo ./install.sh

# 3. Verify installation
ls -la /opt/node-agent/
ls -la /etc/node-agent/

# 4. Check service files
# Linux:
sudo systemctl status node-agent
# macOS:
sudo launchctl list | grep node-agent
```

### ✅ Registration Process

```bash
# 1. Obtain registration token from management system
# Token format: encoded string valid for 30 minutes

# 2. Run registration
python3 /opt/node-agent/register.py

# 3. Verify configuration created
cat /etc/node-agent/config.json

# 4. Test connectivity
curl -k https://your-management-system.com/health
```

## Post-Installation Verification

### ✅ Service Status

```bash
# Linux (systemd)
sudo systemctl start node-agent
sudo systemctl enable node-agent
sudo systemctl status node-agent

# macOS (launchd)
sudo launchctl load /Library/LaunchDaemons/com.ai-stock-trader.node-agent.plist
sudo launchctl start com.ai-stock-trader.node-agent
sudo launchctl list | grep node-agent
```

### ✅ Data Collection

```bash
# Wait 2-3 minutes for initial data collection
python3 /opt/node-agent/data_manager.py stats

# Expected output:
# Database Statistics
# ===================
# File: /opt/node-agent/data/agent.db
# Size: X.X MB
# Tables: 6
# Total records: XX+
```

### ✅ Log Verification

```bash
# Check logs for errors
# Linux:
sudo journalctl -u node-agent -n 50

# macOS:
tail -f /opt/node-agent/logs/agent.log

# Look for:
# ✓ "Agent started successfully"
# ✓ "Resource monitoring started"
# ✓ "Communication manager initialized"
# ✓ No ERROR level messages
```

### ✅ Security Validation

```bash
# Verify file permissions
ls -la /opt/node-agent/data/
# Should show: drwx------ (700)

ls -la /etc/node-agent/config.json
# Should show: -rw-r----- (640)

# Verify encryption
python3 /opt/node-agent/data_manager.py verify
# Should show: "✓ All data integrity checks passed"
```

## Performance Validation

### ✅ Resource Usage

```bash
# Check agent memory usage
ps aux | grep agent.py

# Check database size
du -h /opt/node-agent/data/

# Verify no excessive CPU usage
top -p $(pgrep -f agent.py)
```

### ✅ Data Management

```bash
# Test data export
python3 /opt/node-agent/data_manager.py export-metrics --output test_metrics.csv

# Test cleanup (dry run)
python3 /opt/node-agent/data_manager.py cleanup --days 30 --dry-run

# Verify data integrity
python3 /opt/node-agent/data_manager.py verify
```

## Network Connectivity Tests

### ✅ Management System Communication

```bash
# Test basic connectivity
curl -k https://your-management-system.com/health

# Test with agent credentials (if available)
curl -k -H "Authorization: Bearer YOUR_API_KEY" \
     https://your-management-system.com/api/devices/status

# Check WebSocket connectivity (if applicable)
# This would be done through the agent logs
```

### ✅ DNS Resolution

```bash
# Verify DNS resolution for management system
nslookup your-management-system.com
dig your-management-system.com
```

## Troubleshooting Common Issues

### ❌ Permission Denied Errors

```bash
# Fix ownership
sudo chown -R node-agent:node-agent /opt/node-agent

# Fix permissions
sudo chmod 750 /opt/node-agent
sudo chmod 700 /opt/node-agent/data
sudo chmod 640 /etc/node-agent/config.json
```

### ❌ Service Won't Start

```bash
# Check Python path
which python3
python3 --version

# Verify dependencies
python3 -c "import psutil, cryptography, aiohttp; print('Dependencies OK')"

# Check configuration
python3 -c "import json; print(json.load(open('/etc/node-agent/config.json')))"

# Test manually
cd /opt/node-agent
python3 agent.py --test
```

### ❌ Database Issues

```bash
# Check database file exists and is readable
ls -la /opt/node-agent/data/agent.db*

# Test database connection
python3 -c "
import sqlite3
import os
db_path = '/opt/node-agent/data/agent.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    print('Database connection OK')
    conn.close()
else:
    print('Database file not found')
"

# Rebuild database if corrupted
cd /opt/node-agent
python3 -c "
import asyncio
from data_store import SecureDataStore
async def rebuild():
    store = SecureDataStore('/opt/node-agent/data/agent_new.db')
    await store.initialize()
    print('New database created')
    await store.close()
asyncio.run(rebuild())
"
```

### ❌ Network Issues

```bash
# Test connectivity with verbose output
curl -v -k https://your-management-system.com/health

# Check firewall rules
# Linux:
sudo iptables -L | grep -E '(443|80)'
# macOS:
sudo pfctl -sr | grep -E '(443|80)'

# Test DNS resolution
nslookup your-management-system.com
```

## Production Monitoring

### ✅ Health Checks

```bash
# Create monitoring script
cat > /opt/node-agent/health_check.sh << 'EOF'
#!/bin/bash
# Basic health check for node-agent

# Check if process is running
if ! pgrep -f "agent.py" > /dev/null; then
    echo "ERROR: Agent process not running"
    exit 1
fi

# Check if database is accessible
if ! python3 -c "
import sqlite3
import os
db_path = '/opt/node-agent/data/agent.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.close()
    print('Database OK')
else:
    exit(1)
" > /dev/null 2>&1; then
    echo "ERROR: Database not accessible"
    exit 1
fi

# Check disk space
USAGE=$(df /opt/node-agent | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $USAGE -gt 90 ]; then
    echo "WARNING: Disk usage at ${USAGE}%"
fi

echo "OK: Agent healthy"
EOF

chmod +x /opt/node-agent/health_check.sh
```

### ✅ Log Rotation

```bash
# Setup logrotate (Linux)
sudo cat > /etc/logrotate.d/node-agent << 'EOF'
/opt/node-agent/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

# Test logrotate
sudo logrotate -d /etc/logrotate.d/node-agent
```

### ✅ Automated Cleanup

```bash
# Create cron job for data cleanup
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/bin/python3 /opt/node-agent/data_manager.py cleanup --days 30") | crontab -

# Verify cron job
crontab -l | grep node-agent
```

## Final Validation Checklist

- [ ] All tests pass (`python3 test_agent.py`)
- [ ] Service starts automatically (`systemctl enable node-agent`)
- [ ] Data collection working (check `data_manager.py stats`)
- [ ] Logs show no errors
- [ ] Network connectivity to management system confirmed
- [ ] Registration completed successfully
- [ ] File permissions secure
- [ ] Monitoring and health checks configured
- [ ] Log rotation configured
- [ ] Automated cleanup scheduled

## Production Support

### Emergency Procedures

```bash
# Stop agent immediately
sudo systemctl stop node-agent  # Linux
sudo launchctl stop com.ai-stock-trader.node-agent  # macOS

# Export data before maintenance
python3 /opt/node-agent/data_manager.py export-json emergency_backup.json

# Restart with debug logging
export NODE_AGENT_LOG_LEVEL="DEBUG"
sudo systemctl restart node-agent
```

### Performance Tuning

```bash
# Adjust collection interval (in config.json)
"collection_interval": 300  # 5 minutes instead of 1 minute

# Reduce data retention
python3 /opt/node-agent/data_manager.py cleanup --days 7

# Monitor resource usage
watch 'ps aux | grep agent.py'
```

This checklist ensures a smooth production deployment of the Node Agent with proper security, monitoring, and maintenance procedures.

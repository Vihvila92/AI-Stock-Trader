#!/bin/bash

# Node-Agent Installation Script
# Supports Ubuntu and macOS - Works on completely clean systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_USER="node-agent"
AGENT_DIR="/opt/node-agent"
CONFIG_DIR="/etc/node-agent"
LOG_DIR="/var/log/node-agent"
SERVICE_NAME="node-agent"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "========================================"
    echo "    AI Stock Trader - Node Agent"
    echo "         Installation Script"
    echo "========================================"
    echo -e "${NC}"
    echo ""
}

# Detect OS
detect_os() {
    echo -e "${YELLOW}Detecting operating system...${NC}"

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            OS="ubuntu"
            DISTRO_NAME=$(lsb_release -si 2>/dev/null || echo "Ubuntu")
            DISTRO_VERSION=$(lsb_release -sr 2>/dev/null || echo "Unknown")
        elif command -v yum &> /dev/null; then
            OS="centos"
            DISTRO_NAME="CentOS/RHEL"
        else
            echo -e "${RED}Unsupported Linux distribution${NC}"
            echo "This script supports Ubuntu/Debian and CentOS/RHEL systems"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO_NAME="macOS"
        DISTRO_VERSION=$(sw_vers -productVersion 2>/dev/null || echo "Unknown")
    else
        echo -e "${RED}Unsupported operating system: $OSTYPE${NC}"
        echo "This script supports Ubuntu, CentOS, and macOS"
        exit 1
    fi

    echo -e "${GREEN}✓ Detected: $DISTRO_NAME $DISTRO_VERSION${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}✗ This script must be run as root (use sudo)${NC}"
        echo "Please run: sudo $0"
        exit 1
    fi
    echo -e "${GREEN}✓ Running with root privileges${NC}"
}

# Install Homebrew on macOS
install_homebrew() {
    echo -e "${YELLOW}Installing Homebrew...${NC}"

    # Get the actual user who ran sudo
    ACTUAL_USER="${SUDO_USER:-$(logname 2>/dev/null || whoami)}"
    ACTUAL_HOME=$(eval echo "~$ACTUAL_USER")

    # Check if Homebrew is already installed
    if [[ -x "/opt/homebrew/bin/brew" ]] || [[ -x "/usr/local/bin/brew" ]] || command -v brew &> /dev/null; then
        echo -e "${GREEN}✓ Homebrew already installed${NC}"
        # Update Homebrew
        echo -e "${YELLOW}Updating Homebrew...${NC}"
        sudo -u "$ACTUAL_USER" -H bash -c 'export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" && brew update' || true
        return
    fi

    # Check if user has command line tools
    echo -e "${YELLOW}Checking for Xcode Command Line Tools...${NC}"
    if ! xcode-select -p &> /dev/null; then
        echo -e "${YELLOW}Installing Xcode Command Line Tools...${NC}"
        xcode-select --install
        echo "Please complete the Xcode Command Line Tools installation and run this script again."
        exit 1
    fi

    # Install Homebrew as the actual user (not root)
    echo -e "${YELLOW}Installing Homebrew as user $ACTUAL_USER...${NC}"
    sudo -u "$ACTUAL_USER" -H bash -c 'NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'

    # Add Homebrew to PATH
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        # Apple Silicon Mac
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$ACTUAL_HOME/.zprofile"
        export PATH="/opt/homebrew/bin:$PATH"
    elif [[ -f "/usr/local/bin/brew" ]]; then
        # Intel Mac
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> "$ACTUAL_HOME/.bash_profile"
        export PATH="/usr/local/bin:$PATH"
    fi

    echo -e "${GREEN}✓ Homebrew installed successfully${NC}"
}

# Install system dependencies
install_dependencies() {
    echo -e "${YELLOW}Installing system dependencies...${NC}"

    case $OS in
        ubuntu)
            # Update package list
            echo -e "${YELLOW}Updating package lists...${NC}"
            apt-get update -qq

            # Install essential packages first
            echo -e "${YELLOW}Installing essential packages...${NC}"
            apt-get install -y \
                curl \
                wget \
                git \
                software-properties-common \
                apt-transport-https \
                ca-certificates \
                gnupg \
                lsb-release \
                systemd \
                sudo

            # Check Ubuntu version and install Python accordingly
            UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "20.04")
            echo -e "${YELLOW}Installing Python for Ubuntu $UBUNTU_VERSION...${NC}"

            # Install Python and development tools
            apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                build-essential \
                openssl \
                libssl-dev \
                libffi-dev \
                pkg-config \
                python3-distutils

            # For older Ubuntu versions, ensure we have python3-venv
            if ! dpkg -l | grep -q python3-venv; then
                apt-get install -y python3.8-venv 2>/dev/null || \
                apt-get install -y python3.9-venv 2>/dev/null || \
                apt-get install -y python3.10-venv 2>/dev/null || \
                apt-get install -y python3.11-venv 2>/dev/null || {
                    echo -e "${YELLOW}Installing python3-venv manually...${NC}"
                    python3 -m pip install --user virtualenv
                }
            fi

            # Ensure pip is up to date
            python3 -m pip install --upgrade pip
            echo -e "${GREEN}✓ Ubuntu dependencies installed${NC}"
            ;;

        centos)
            # Update package list
            echo -e "${YELLOW}Updating package lists...${NC}"
            yum update -y -q

            # Install EPEL repository for additional packages
            yum install -y epel-release

            # Install essential packages
            echo -e "${YELLOW}Installing essential packages...${NC}"
            yum install -y \
                curl \
                wget \
                git \
                systemd \
                sudo \
                python3 \
                python3-pip \
                python3-devel \
                gcc \
                gcc-c++ \
                make \
                openssl \
                openssl-devel \
                libffi-devel \
                pkgconfig

            # Ensure pip is up to date
            python3 -m pip install --upgrade pip
            echo -e "${GREEN}✓ CentOS dependencies installed${NC}"
            ;;

        macos)
            # Install Homebrew if not present
            install_homebrew

            # Install essential packages
            echo -e "${YELLOW}Installing essential packages...${NC}"

            # Get the actual user
            ACTUAL_USER="${SUDO_USER:-$(logname 2>/dev/null || whoami)}"

            # Set up PATH for brew commands
            export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

            # Install packages
            packages=(python3 curl wget git openssl libffi pkg-config)
            for package in "${packages[@]}"; do
                echo -e "${YELLOW}Installing $package...${NC}"
                if ! sudo -u "$ACTUAL_USER" -H bash -c "export PATH=\"/opt/homebrew/bin:/usr/local/bin:\$PATH\" && brew list $package" &> /dev/null; then
                    sudo -u "$ACTUAL_USER" -H bash -c "export PATH=\"/opt/homebrew/bin:/usr/local/bin:\$PATH\" && brew install $package" || {
                        echo -e "${RED}Failed to install $package${NC}"
                        # Don't exit for optional packages
                    }
                else
                    echo -e "${GREEN}✓ $package already installed${NC}"
                fi
            done

            # Ensure pip is up to date
            python3 -m pip install --upgrade pip --break-system-packages 2>/dev/null || python3 -m pip install --upgrade pip
            echo -e "${GREEN}✓ macOS dependencies installed${NC}"
            ;;
    esac
}

# Create system user
create_user() {
    if [[ "$OS" != "macos" ]]; then
        echo -e "${YELLOW}Creating system user: $AGENT_USER${NC}"

        if ! id "$AGENT_USER" &>/dev/null; then
            useradd --system --shell /bin/false --home-dir "$AGENT_DIR" --create-home "$AGENT_USER"
            echo -e "${GREEN}✓ Created user: $AGENT_USER${NC}"
        else
            echo -e "${GREEN}✓ User $AGENT_USER already exists${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping user creation on macOS (will run as root)${NC}"
    fi
}

# Create directories
create_directories() {
    echo -e "${YELLOW}Creating directories...${NC}"

    # Create all required directories
    mkdir -p "$AGENT_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$AGENT_DIR/modules"
    mkdir -p "$AGENT_DIR/src"

    # Set permissions
    if [[ "$OS" != "macos" ]]; then
        chown -R "$AGENT_USER:$AGENT_USER" "$AGENT_DIR"
        chown -R "$AGENT_USER:$AGENT_USER" "$CONFIG_DIR"
        chown -R "$AGENT_USER:$AGENT_USER" "$LOG_DIR"
        chmod 755 "$AGENT_DIR"
        chmod 755 "$CONFIG_DIR"
        chmod 755 "$LOG_DIR"
    else
        # On macOS, use root ownership
        chown -R root:wheel "$AGENT_DIR"
        chown -R root:wheel "$CONFIG_DIR"
        chown -R root:wheel "$LOG_DIR"
        chmod 755 "$AGENT_DIR"
        chmod 755 "$CONFIG_DIR"
        chmod 755 "$LOG_DIR"
    fi

    echo -e "${GREEN}✓ Directories created and configured${NC}"
}

# Install Python dependencies
install_python_deps() {
    echo -e "${YELLOW}Installing Python dependencies...${NC}"

    # Ensure we have the requirements file
    REQUIREMENTS_FILE="$(dirname "$0")/requirements.txt"
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        echo -e "${RED}Error: requirements.txt not found at $REQUIREMENTS_FILE${NC}"
        exit 1
    fi

    # Create virtual environment
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv "$AGENT_DIR/venv"

    # Activate and install dependencies
    echo -e "${YELLOW}Installing Python packages...${NC}"
    source "$AGENT_DIR/venv/bin/activate"

    # Upgrade pip first
    pip install --upgrade pip

    # Install wheel for better package building
    pip install wheel

    # Install packages from requirements.txt
    pip install -r "$REQUIREMENTS_FILE"

    # Set ownership
    if [[ "$OS" != "macos" ]]; then
        chown -R "$AGENT_USER:$AGENT_USER" "$AGENT_DIR/venv"
    else
        chown -R root:wheel "$AGENT_DIR/venv"
    fi

    echo -e "${GREEN}✓ Python dependencies installed${NC}"
}

# Copy agent files
copy_agent_files() {
    echo -e "${YELLOW}Copying agent files...${NC}"

    SCRIPT_DIR="$(dirname "$0")"

    # Check if source files exist
    if [[ ! -d "$SCRIPT_DIR/src" ]]; then
        echo -e "${RED}Error: src directory not found at $SCRIPT_DIR/src${NC}"
        exit 1
    fi

    if [[ ! -f "$SCRIPT_DIR/register.py" ]]; then
        echo -e "${RED}Error: register.py not found at $SCRIPT_DIR/register.py${NC}"
        exit 1
    fi

    if [[ ! -f "$SCRIPT_DIR/data_manager.py" ]]; then
        echo -e "${RED}Error: data_manager.py not found at $SCRIPT_DIR/data_manager.py${NC}"
        exit 1
    fi

    # Copy source files to appropriate locations
    cp -r "$SCRIPT_DIR/src"/* "$AGENT_DIR/"
    cp "$SCRIPT_DIR/register.py" "$AGENT_DIR/"
    cp "$SCRIPT_DIR/data_manager.py" "$AGENT_DIR/"

    # Make scripts executable
    chmod +x "$AGENT_DIR/agent.py"
    chmod +x "$AGENT_DIR/register.py"
    chmod +x "$AGENT_DIR/data_manager.py"

    # Set ownership
    if [[ "$OS" != "macos" ]]; then
        chown -R "$AGENT_USER:$AGENT_USER" "$AGENT_DIR"
    else
        chown -R root:wheel "$AGENT_DIR"
    fi

    echo -e "${GREEN}✓ Agent files copied${NC}"
}

# Initialize secure database and credentials
initialize_database() {
    echo -e "${YELLOW}Initializing secure database and credentials...${NC}"

    # Create data directory for database
    mkdir -p "$AGENT_DIR/data"

    # Set ownership and permissions for data directory
    if [[ "$OS" != "macos" ]]; then
        chown -R "$AGENT_USER:$AGENT_USER" "$AGENT_DIR/data"
        chmod 750 "$AGENT_DIR/data"
    else
        chown -R root:wheel "$AGENT_DIR/data"
        chmod 750 "$AGENT_DIR/data"
    fi

    # Initialize database and generate credentials using the data manager
    echo -e "${YELLOW}Setting up database schema and generating initial credentials...${NC}"

    # Run database initialization
    DB_PATH="$AGENT_DIR/data/agent.db"

    if [[ "$OS" != "macos" ]]; then
        # Run as the agent user on Linux
        sudo -u "$AGENT_USER" "$AGENT_DIR/venv/bin/python" "$AGENT_DIR/data_manager.py" --db-path "$DB_PATH" init-credentials
    else
        # Run as root on macOS
        "$AGENT_DIR/venv/bin/python" "$AGENT_DIR/data_manager.py" --db-path "$DB_PATH" init-credentials
    fi

    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓ Database initialized and credentials generated${NC}"
    else
        echo -e "${RED}✗ Failed to initialize database${NC}"
        echo "You can manually initialize it later by running:"
        echo "  $AGENT_DIR/venv/bin/python $AGENT_DIR/data_manager.py --db-path $DB_PATH init-credentials"
    fi

    # Set final permissions on database file
    if [[ -f "$DB_PATH" ]]; then
        if [[ "$OS" != "macos" ]]; then
            chown "$AGENT_USER:$AGENT_USER" "$DB_PATH"
            chmod 600 "$DB_PATH"
        else
            chown root:wheel "$DB_PATH"
            chmod 600 "$DB_PATH"
        fi
    fi

    echo -e "${GREEN}✓ Secure database setup completed${NC}"
}

# Create systemd service (Linux)
create_systemd_service() {
    echo -e "${YELLOW}Creating systemd service...${NC}"

    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Node-Agent for AI Stock Trader
After=network.target
Wants=network.target

[Service]
Type=simple
User=$AGENT_USER
Group=$AGENT_USER
WorkingDirectory=$AGENT_DIR
Environment=PATH=$AGENT_DIR/venv/bin
Environment=AGENT_DB_PATH=$AGENT_DIR/data/agent.db
Environment=AGENT_LOG_DIR=$LOG_DIR
Environment=AGENT_CONFIG_DIR=$CONFIG_DIR
ExecStart=$AGENT_DIR/venv/bin/python $AGENT_DIR/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=node-agent

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$AGENT_DIR $CONFIG_DIR $LOG_DIR /tmp

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
}

# Create launchd service (macOS)
create_launchd_service() {
    echo -e "${YELLOW}Creating launchd service...${NC}"

    cat > "/Library/LaunchDaemons/com.aistocktrader.${SERVICE_NAME}.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aistocktrader.${SERVICE_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>$AGENT_DIR/venv/bin/python</string>
        <string>$AGENT_DIR/agent.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$AGENT_DIR</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>AGENT_DB_PATH</key>
        <string>$AGENT_DIR/data/agent.db</string>
        <key>AGENT_LOG_DIR</key>
        <string>$LOG_DIR</string>
        <key>AGENT_CONFIG_DIR</key>
        <string>$CONFIG_DIR</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/node-agent.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/node-agent-error.log</string>
</dict>
</plist>
EOF

    # Load the service
    launchctl load "/Library/LaunchDaemons/com.aistocktrader.${SERVICE_NAME}.plist"
}

# Register agent
register_agent() {
    echo -e "${YELLOW}Agent installation completed!${NC}"
    echo ""
    echo -e "${GREEN}✓ Secure database initialized with agent credentials${NC}"
    echo -e "${GREEN}✓ Configuration management system ready${NC}"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Get a registration token from your management system"
    echo "2. Run the registration command:"
    echo "   sudo $AGENT_DIR/venv/bin/python $AGENT_DIR/register.py"
    echo ""
    echo -e "${GREEN}Configuration management:${NC}"
    echo "View config:     sudo $AGENT_DIR/venv/bin/python $AGENT_DIR/data_manager.py --db-path $AGENT_DIR/data/agent.db show-config"
    echo "Set config:      sudo $AGENT_DIR/venv/bin/python $AGENT_DIR/data_manager.py --db-path $AGENT_DIR/data/agent.db set-config <key> <value>"
    echo "View credentials: sudo $AGENT_DIR/venv/bin/python $AGENT_DIR/data_manager.py --db-path $AGENT_DIR/data/agent.db show-credentials"
    echo "Database stats:  sudo $AGENT_DIR/venv/bin/python $AGENT_DIR/data_manager.py --db-path $AGENT_DIR/data/agent.db stats"
    echo ""
    echo -e "${GREEN}Service management:${NC}"

    case $OS in
        ubuntu|centos)
            echo "Start:   sudo systemctl start $SERVICE_NAME"
            echo "Stop:    sudo systemctl stop $SERVICE_NAME"
            echo "Status:  sudo systemctl status $SERVICE_NAME"
            echo "Logs:    sudo journalctl -u $SERVICE_NAME -f"
            ;;
        macos)
            echo "Start:   sudo launchctl load /Library/LaunchDaemons/com.aistocktrader.${SERVICE_NAME}.plist"
            echo "Stop:    sudo launchctl unload /Library/LaunchDaemons/com.aistocktrader.${SERVICE_NAME}.plist"
            echo "Logs:    tail -f $LOG_DIR/node-agent.log"
            ;;
    esac
}

# Main installation function
main() {
    print_banner
    echo -e "${GREEN}Node-Agent Installation Script${NC}"
    echo "================================"

    # Check for required parameters
    if [[ $# -gt 0 && "$1" == "--help" ]]; then
        echo ""
        echo "Usage: sudo $0"
        echo ""
        echo "This script will install the Node-Agent on your system."
        echo "Supported platforms: Ubuntu, CentOS, macOS"
        echo ""
        echo "Requirements:"
        echo "- Root privileges (run with sudo)"
        echo "- Internet connection"
        echo "- Clean system or existing installation"
        echo ""
        exit 0
    fi

    # Validate environment
    echo -e "${YELLOW}Validating installation environment...${NC}"

    detect_os
    check_root

    # Check internet connectivity
    echo -e "${YELLOW}Checking internet connectivity...${NC}"
    if ! curl -s --connect-timeout 5 https://google.com > /dev/null; then
        echo -e "${RED}✗ No internet connection detected${NC}"
        echo "Internet access is required for downloading dependencies"
        exit 1
    fi
    echo -e "${GREEN}✓ Internet connection verified${NC}"

    # Start installation
    echo ""
    echo -e "${BLUE}Starting installation process...${NC}"

    install_dependencies
    create_user
    create_directories
    install_python_deps
    copy_agent_files
    initialize_database

    case $OS in
        ubuntu|centos)
            create_systemd_service
            ;;
        macos)
            create_launchd_service
            ;;
    esac

    register_agent

    echo ""
    echo -e "${GREEN}✓ Installation completed successfully!${NC}"
}

# Run main function
main "$@"

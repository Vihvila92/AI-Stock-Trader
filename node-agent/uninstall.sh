#!/bin/bash

# Node-Agent Uninstallation Script
# Safely removes all Node-Agent components from the system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration (must match install.sh)
AGENT_USER="node-agent"
AGENT_DIR="/opt/node-agent"
CONFIG_DIR="/etc/node-agent"
LOG_DIR="/var/log/node-agent"
SERVICE_NAME="node-agent"

# Uninstall options
REMOVE_DEPENDENCIES=false
FORCE_MODE=false
NO_BACKUP=false

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "========================================"
    echo "    AI Stock Trader - Node Agent"
    echo "        Uninstallation Script"
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
        elif command -v yum &> /dev/null; then
            OS="centos"
            DISTRO_NAME="CentOS/RHEL"
        else
            OS="linux"
            DISTRO_NAME="Linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO_NAME="macOS"
    else
        OS="unknown"
        DISTRO_NAME="Unknown OS"
    fi

    echo -e "${GREEN}✓ Detected: $DISTRO_NAME${NC}"
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

# Stop and disable systemd service (Linux)
stop_systemd_service() {
    echo -e "${YELLOW}Stopping and disabling systemd service...${NC}"

    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

    if [[ -f "$SERVICE_FILE" ]]; then
        # Stop the service if running
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            echo "Stopping $SERVICE_NAME service..."
            systemctl stop "$SERVICE_NAME"
        fi

        # Disable the service
        if systemctl is-enabled --quiet "$SERVICE_NAME"; then
            echo "Disabling $SERVICE_NAME service..."
            systemctl disable "$SERVICE_NAME"
        fi

        # Remove service file
        echo "Removing service file..."
        rm -f "$SERVICE_FILE"

        # Reload systemd
        systemctl daemon-reload
        systemctl reset-failed

        echo -e "${GREEN}✓ Systemd service removed${NC}"
    else
        echo -e "${YELLOW}No systemd service found${NC}"
    fi
}

# Stop and remove launchd service (macOS)
stop_launchd_service() {
    echo -e "${YELLOW}Stopping and removing launchd service...${NC}"

    PLIST_FILE="/Library/LaunchDaemons/com.aistocktrader.${SERVICE_NAME}.plist"

    if [[ -f "$PLIST_FILE" ]]; then
        # Unload the service if loaded
        if launchctl list | grep -q "com.aistocktrader.${SERVICE_NAME}"; then
            echo "Unloading launchd service..."
            launchctl unload "$PLIST_FILE" 2>/dev/null || true
        fi

        # Remove plist file
        echo "Removing plist file..."
        rm -f "$PLIST_FILE"

        echo -e "${GREEN}✓ Launchd service removed${NC}"
    else
        echo -e "${YELLOW}No launchd service found${NC}"
    fi
}

# Remove directories and files
remove_files() {
    echo -e "${YELLOW}Removing installation directories...${NC}"

    # Stop any running processes that might be using the files
    pkill -f "python.*agent.py" 2>/dev/null || true
    pkill -f "python.*register.py" 2>/dev/null || true
    pkill -f "python.*data_manager.py" 2>/dev/null || true

    # Wait a moment for processes to stop
    sleep 2

    # Remove directories
    directories=("$AGENT_DIR" "$CONFIG_DIR" "$LOG_DIR")

    for dir in "${directories[@]}"; do
        if [[ -d "$dir" ]]; then
            echo "Removing directory: $dir"
            rm -rf "$dir"
        else
            echo "Directory not found: $dir"
        fi
    done

    echo -e "${GREEN}✓ Installation directories removed${NC}"
}

# Remove system user (Linux only)
remove_user() {
    if [[ "$OS" != "macos" ]]; then
        echo -e "${YELLOW}Removing system user: $AGENT_USER${NC}"

        if id "$AGENT_USER" &>/dev/null; then
            # Kill any processes running as the user
            pkill -u "$AGENT_USER" 2>/dev/null || true
            sleep 1

            # Remove the user
            userdel "$AGENT_USER" 2>/dev/null || true

            # Remove user's group if it exists and is empty
            if getent group "$AGENT_USER" &>/dev/null; then
                groupdel "$AGENT_USER" 2>/dev/null || true
            fi

            echo -e "${GREEN}✓ User $AGENT_USER removed${NC}"
        else
            echo -e "${YELLOW}User $AGENT_USER not found${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping user removal on macOS${NC}"
    fi
}

# Backup important data
backup_data() {
    echo -e "${YELLOW}Checking for important data to backup...${NC}"

    BACKUP_DIR="/tmp/node-agent-backup-$(date +%Y%m%d-%H%M%S)"
    DB_FILE="$AGENT_DIR/data/agent.db"

    # Check if there's anything to backup
    backup_needed=false

    if [[ -f "$DB_FILE" ]]; then
        backup_needed=true
    fi

    if [[ -d "$CONFIG_DIR" ]] && [[ -n "$(ls -A "$CONFIG_DIR" 2>/dev/null)" ]]; then
        backup_needed=true
    fi

    if [[ -d "$LOG_DIR" ]] && [[ -n "$(ls -A "$LOG_DIR" 2>/dev/null)" ]]; then
        backup_needed=true
    fi

    if [[ "$backup_needed" == "true" ]]; then
        echo "Creating backup at: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"

        # Backup database
        if [[ -f "$DB_FILE" ]]; then
            echo "Backing up database..."
            cp "$DB_FILE" "$BACKUP_DIR/"
        fi

        # Backup config files
        if [[ -d "$CONFIG_DIR" ]] && [[ -n "$(ls -A "$CONFIG_DIR" 2>/dev/null)" ]]; then
            echo "Backing up configuration files..."
            cp -r "$CONFIG_DIR" "$BACKUP_DIR/"
        fi

        # Backup logs (last 100 lines of each log file)
        if [[ -d "$LOG_DIR" ]] && [[ -n "$(ls -A "$LOG_DIR" 2>/dev/null)" ]]; then
            echo "Backing up recent logs..."
            mkdir -p "$BACKUP_DIR/logs"
            for logfile in "$LOG_DIR"/*.log; do
                if [[ -f "$logfile" ]]; then
                    tail -n 100 "$logfile" > "$BACKUP_DIR/logs/$(basename "$logfile")" 2>/dev/null || true
                fi
            done
        fi

        echo -e "${GREEN}✓ Important data backed up to: $BACKUP_DIR${NC}"
        echo -e "${YELLOW}Note: You can remove this backup manually when no longer needed${NC}"
    else
        echo -e "${YELLOW}No important data found to backup${NC}"
    fi
}

# Clean up Python packages (optional)
cleanup_python_packages() {
    echo -e "${YELLOW}Checking for Python package cleanup...${NC}"

    if [[ "$REMOVE_DEPENDENCIES" == "true" ]]; then
        echo -e "${YELLOW}Removing Python packages installed for Node-Agent...${NC}"

        # Remove packages from requirements.txt if available
        REQUIREMENTS_FILE="$(dirname "$0")/requirements.txt"
        if [[ -f "$REQUIREMENTS_FILE" ]]; then
            echo "Removing Python packages from requirements.txt..."
            # Use pip to uninstall packages (if pip is available)
            if command -v pip3 &> /dev/null; then
                pip3 uninstall -r "$REQUIREMENTS_FILE" -y 2>/dev/null || true
            elif command -v pip &> /dev/null; then
                pip uninstall -r "$REQUIREMENTS_FILE" -y 2>/dev/null || true
            fi
        fi

        echo -e "${GREEN}✓ Python packages cleanup attempted${NC}"
    else
        # This is optional since packages might be used by other applications
        echo -e "${YELLOW}Skipping Python package removal (use --remove-dependencies to remove)${NC}"
        echo "Note: Python packages are left installed as they may be used by other applications."
        echo "Use --remove-dependencies flag to remove all dependencies installed by install.sh"
    fi
}

# Remove system dependencies (only with --remove-dependencies)
remove_system_dependencies() {
    if [[ "$REMOVE_DEPENDENCIES" != "true" ]]; then
        return 0
    fi

    echo -e "${YELLOW}Removing system dependencies installed by install.sh...${NC}"
    echo -e "${RED}WARNING: This will remove system packages that may be used by other applications!${NC}"

    case $OS in
        ubuntu)
            echo -e "${YELLOW}Removing Ubuntu packages (only non-essential ones)...${NC}"
            # Only remove packages that are specific to development and not essential
            packages_to_remove=(
                "python3-dev"
                "build-essential"
                "libssl-dev"
                "libffi-dev"
                "pkg-config"
                "python3-distutils"
            )

            # Check which packages are installed and safe to remove
            for package in "${packages_to_remove[@]}"; do
                if dpkg -l | grep -q "^ii.*$package "; then
                    echo "Removing $package..."
                    apt-get remove -y "$package" 2>/dev/null || {
                        echo -e "${YELLOW}Could not remove $package (may be required by other packages)${NC}"
                    }
                fi
            done

            # Clean up
            apt-get autoremove -y 2>/dev/null || true
            echo -e "${GREEN}✓ Ubuntu development packages removed${NC}"
            ;;

        centos)
            echo -e "${YELLOW}Removing CentOS packages (only non-essential ones)...${NC}"
            packages_to_remove=(
                "python3-devel"
                "gcc"
                "gcc-c++"
                "make"
                "openssl-devel"
                "libffi-devel"
                "pkgconfig"
            )

            for package in "${packages_to_remove[@]}"; do
                if rpm -q "$package" &>/dev/null; then
                    echo "Removing $package..."
                    yum remove -y "$package" 2>/dev/null || {
                        echo -e "${YELLOW}Could not remove $package (may be required by other packages)${NC}"
                    }
                fi
            done
            echo -e "${GREEN}✓ CentOS development packages removed${NC}"
            ;;

        macos)
            echo -e "${YELLOW}Removing Homebrew packages installed for Node-Agent...${NC}"

            # Get the actual user who ran sudo
            ACTUAL_USER="${SUDO_USER:-$(logname 2>/dev/null || whoami)}"

            # Set up PATH for brew commands
            export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

            # List of packages that were installed specifically for node-agent
            packages_to_remove=(
                "pkg-config"
                "libffi"
            )

            for package in "${packages_to_remove[@]}"; do
                if sudo -u "$ACTUAL_USER" -H bash -c "export PATH=\"/opt/homebrew/bin:/usr/local/bin:\$PATH\" && brew list $package" &> /dev/null; then
                    echo "Removing $package..."
                    sudo -u "$ACTUAL_USER" -H bash -c "export PATH=\"/opt/homebrew/bin:/usr/local/bin:\$PATH\" && brew uninstall $package" 2>/dev/null || {
                        echo -e "${YELLOW}Could not remove $package (may be required by other packages)${NC}"
                    }
                fi
            done

            echo -e "${YELLOW}Note: Core packages like Python3, git, curl, wget, and openssl are left installed${NC}"
            echo -e "${YELLOW}Note: Homebrew itself is left installed as it may be used by other applications${NC}"
            echo -e "${GREEN}✓ Node-Agent specific Homebrew packages removed${NC}"
            ;;
    esac

    echo -e "${GREEN}✓ System dependencies cleanup completed${NC}"
}

# Verify removal
verify_removal() {
    echo -e "${YELLOW}Verifying removal...${NC}"

    # Check for remaining files
    remaining_files=()

    if [[ -d "$AGENT_DIR" ]]; then
        remaining_files+=("$AGENT_DIR")
    fi

    if [[ -d "$CONFIG_DIR" ]]; then
        remaining_files+=("$CONFIG_DIR")
    fi

    if [[ -d "$LOG_DIR" ]]; then
        remaining_files+=("$LOG_DIR")
    fi

    # Check for service files
    case $OS in
        ubuntu|centos|linux)
            if [[ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]]; then
                remaining_files+=("/etc/systemd/system/${SERVICE_NAME}.service")
            fi
            ;;
        macos)
            if [[ -f "/Library/LaunchDaemons/com.aistocktrader.${SERVICE_NAME}.plist" ]]; then
                remaining_files+=("/Library/LaunchDaemons/com.aistocktrader.${SERVICE_NAME}.plist")
            fi
            ;;
    esac

    # Check for running processes
    if pgrep -f "python.*agent.py" >/dev/null 2>&1; then
        remaining_files+=("Running agent processes")
    fi

    if [[ ${#remaining_files[@]} -eq 0 ]]; then
        echo -e "${GREEN}✓ All components successfully removed${NC}"
        return 0
    else
        echo -e "${YELLOW}Warning: Some components may still remain:${NC}"
        for item in "${remaining_files[@]}"; do
            echo "  - $item"
        done
        return 1
    fi
}

# Main uninstallation function
main() {
    print_banner
    echo -e "${GREEN}Node-Agent Uninstallation Script${NC}"
    echo "==================================="

    # Check for help
    if [[ $# -gt 0 && "$1" == "--help" ]]; then
        echo ""
        echo "Usage: sudo $0 [OPTIONS]"
        echo ""
        echo "This script will remove Node-Agent components from your system."
        echo ""
        echo "Options:"
        echo "  --force               Skip confirmation prompts"
        echo "  --no-backup          Skip data backup before removal"
        echo "  --remove-dependencies Remove system dependencies installed by install.sh"
        echo "  --help               Show this help message"
        echo ""
        echo "Default behavior (safe mode):"
        echo "- Remove Node-Agent service and files only"
        echo "- Remove configuration and log directories"
        echo "- Remove system user '$AGENT_USER' (Linux only)"
        echo "- Create backup of important data (unless --no-backup)"
        echo "- Keep system dependencies (Python, dev tools, etc.)"
        echo ""
        echo "With --remove-dependencies:"
        echo "- Additionally removes development packages (build-essential, python3-dev, etc.)"
        echo "- Removes Python packages from requirements.txt"
        echo "- Does NOT remove essential packages (Python3, git, curl, wget, openssl)"
        echo "- Does NOT remove package managers (apt, yum, Homebrew)"
        echo ""
        echo -e "${YELLOW}WARNING: --remove-dependencies may affect other applications!${NC}"
        echo -e "${YELLOW}Only use if you're sure these packages aren't needed elsewhere.${NC}"
        echo ""
        exit 0
    fi

    # Parse command line arguments
    for arg in "$@"; do
        case $arg in
            --force)
                FORCE_MODE=true
                ;;
            --no-backup)
                NO_BACKUP=true
                ;;
            --remove-dependencies)
                REMOVE_DEPENDENCIES=true
                ;;
            *)
                echo -e "${RED}Unknown option: $arg${NC}"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Validate environment
    echo -e "${YELLOW}Validating environment...${NC}"
    detect_os
    check_root

    # Confirmation prompt
    if [[ "$FORCE_MODE" != true ]]; then
        echo ""
        echo -e "${YELLOW}This will remove the Node-Agent from your system.${NC}"
        echo ""
        echo "The following will be removed:"
        echo "  - Agent service and all files"
        echo "  - Configuration and log directories"
        echo "  - System user '$AGENT_USER' (Linux only)"
        echo "  - Database and stored credentials"

        if [[ "$REMOVE_DEPENDENCIES" == "true" ]]; then
            echo ""
            echo -e "${RED}ADDITIONAL REMOVAL (--remove-dependencies enabled):${NC}"
            echo "  - Development packages (build tools, headers, etc.)"
            echo "  - Python packages from requirements.txt"
            echo -e "${RED}  ⚠ This may affect other applications using these packages!${NC}"
        else
            echo ""
            echo -e "${GREEN}System dependencies will be preserved (use --remove-dependencies to remove)${NC}"
        fi

        echo ""

        if [[ "$NO_BACKUP" != true ]]; then
            echo -e "${GREEN}Important data will be backed up before removal.${NC}"
        else
            echo -e "${RED}No backup will be created (--no-backup specified).${NC}"
        fi

        echo ""
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Uninstallation cancelled.${NC}"
            exit 0
        fi
    fi

    echo ""
    echo -e "${BLUE}Starting uninstallation process...${NC}"

    # Backup data before removal (unless disabled)
    if [[ "$NO_BACKUP" != true ]]; then
        backup_data
    fi

    # Stop and remove services
    case $OS in
        ubuntu|centos|linux)
            stop_systemd_service
            ;;
        macos)
            stop_launchd_service
            ;;
    esac

    # Remove files and directories
    remove_files

    # Remove user (Linux only)
    remove_user

    # Optional cleanup
    cleanup_python_packages

    # Remove system dependencies if requested
    if [[ "$REMOVE_DEPENDENCIES" == "true" ]]; then
        remove_system_dependencies
    fi

    # Verify removal
    echo ""
    verify_removal

    echo ""
    echo -e "${GREEN}✓ Node-Agent uninstallation completed!${NC}"
    echo ""

    if [[ "$REMOVE_DEPENDENCIES" == "true" ]]; then
        echo -e "${GREEN}Dependencies removed as requested.${NC}"
        echo -e "${YELLOW}Note: Essential packages (Python3, git, etc.) were preserved.${NC}"
    else
        echo -e "${GREEN}System dependencies preserved.${NC}"
        echo -e "${YELLOW}Use --remove-dependencies if you want to remove development packages.${NC}"
    fi

    echo ""
    echo "If you want to reinstall, you can run the install.sh script again."

    if [[ "$NO_BACKUP" != true ]]; then
        echo "Backup data is available in /tmp/node-agent-backup-* directories."
    fi
}

# Run main function
main "$@"

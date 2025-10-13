#!/bin/bash

# ============================================
# scripts/setup/install_dependencies.sh
# Install All Dependencies
# Crypto Trading Signal System
# ============================================

set -e  # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Installing System Dependencies           ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo ""

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        exit 1
    fi
}

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo -e "${YELLOW}Detected OS: $OS${NC}"
echo ""

# ==================== CHECK PREREQUISITES ====================

echo "📋 Checking prerequisites..."
echo ""

# Check Docker
if command_exists docker; then
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
    echo -e "${GREEN}✓${NC} Docker installed (version $DOCKER_VERSION)"
else
    echo -e "${RED}✗${NC} Docker not found"
    echo ""
    echo "Please install Docker:"
    echo "  Linux:   https://docs.docker.com/engine/install/"
    echo "  macOS:   https://docs.docker.com/desktop/install/mac-install/"
    echo "  Windows: https://docs.docker.com/desktop/install/windows-install/"
    exit 1
fi

# Check Docker Compose
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    if command_exists docker-compose; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f4 | cut -d ',' -f1)
    else
        COMPOSE_VERSION=$(docker compose version --short)
    fi
    echo -e "${GREEN}✓${NC} Docker Compose installed (version $COMPOSE_VERSION)"
else
    echo -e "${RED}✗${NC} Docker Compose not found"
    echo ""
    echo "Docker Compose is required. Install it from:"
    echo "https://docs.docker.com/compose/install/"
    exit 1
fi

# Check Git
if command_exists git; then
    GIT_VERSION=$(git --version | cut -d ' ' -f3)
    echo -e "${GREEN}✓${NC} Git installed (version $GIT_VERSION)"
else
    echo -e "${YELLOW}!${NC} Git not found (optional but recommended)"
fi

echo ""
echo -e "${GREEN}✓${NC} All prerequisites met!"
echo ""

# ==================== INSTALL OPTIONAL TOOLS ====================

echo "🔧 Installing optional development tools..."
echo ""

# Node.js (for local development)
if ! command_exists node; then
    echo -e "${YELLOW}!${NC} Node.js not found (optional for local development)"
    read -p "Install Node.js? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$OS" = "linux" ]; then
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
            print_status "Node.js installed"
        elif [ "$OS" = "macos" ]; then
            if command_exists brew; then
                brew install node@18
                print_status "Node.js installed"
            else
                echo -e "${YELLOW}Please install Homebrew first: https://brew.sh/${NC}"
            fi
        fi
    fi
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js installed (version $NODE_VERSION)"
fi

# Python (for local development)
if ! command_exists python3; then
    echo -e "${YELLOW}!${NC} Python 3 not found (optional for local development)"
    read -p "Install Python 3? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$OS" = "linux" ]; then
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
            print_status "Python 3 installed"
        elif [ "$OS" = "macos" ]; then
            if command_exists brew; then
                brew install python@3.11
                print_status "Python 3 installed"
            fi
        fi
    fi
else
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f2)
    echo -e "${GREEN}✓${NC} Python 3 installed (version $PYTHON_VERSION)"
fi

echo ""

# ==================== INSTALL PROJECT DEPENDENCIES ====================

echo "📦 Installing project dependencies..."
echo ""

# Frontend dependencies
if [ -d "./frontend" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    if [ -f "package.json" ]; then
        npm install
        print_status "Frontend dependencies installed"
    fi
    cd ..
fi

# Backend API dependencies
if [ -d "./backend/api-gateway" ]; then
    echo "Installing API gateway dependencies..."
    cd backend/api-gateway
    if [ -f "package.json" ]; then
        npm install
        print_status "API gateway dependencies installed"
    fi
    cd ../..
fi

# Python bot dependencies
if [ -d "./backend/bots" ]; then
    echo "Installing Python bot dependencies..."
    
    # Create virtual environment
    if [ ! -d "./backend/bots/venv" ]; then
        python3 -m venv ./backend/bots/venv
        print_status "Virtual environment created"
    fi
    
    # Activate virtual environment
    source ./backend/bots/venv/bin/activate
    
    # Install shared dependencies
    if [ -f "./backend/bots/shared/requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r ./backend/bots/shared/requirements.txt
        print_status "Shared bot dependencies installed"
    fi
    
    # Install individual bot dependencies
    for bot_dir in ./backend/bots/*/; do
        if [ -f "${bot_dir}requirements.txt" ]; then
            bot_name=$(basename "$bot_dir")
            echo "Installing $bot_name dependencies..."
            pip install -r "${bot_dir}requirements.txt"
            print_status "$bot_name dependencies installed"
        fi
    done
    
    deactivate
fi

echo ""

# ==================== INSTALL SYSTEM TOOLS ====================

echo "🛠️  Installing system tools..."
echo ""

# Install TA-Lib (required for technical analysis)
if ! python3 -c "import talib" 2>/dev/null; then
    echo "Installing TA-Lib..."
    if [ "$OS" = "linux" ]; then
        sudo apt-get install -y wget build-essential
        cd /tmp
        wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
        tar -xzf ta-lib-0.4.0-src.tar.gz
        cd ta-lib
        ./configure --prefix=/usr
        make
        sudo make install
        cd -
        pip3 install TA-Lib
        print_status "TA-Lib installed"
    elif [ "$OS" = "macos" ]; then
        if command_exists brew; then
            brew install ta-lib
            pip3 install TA-Lib
            print_status "TA-Lib installed"
        fi
    fi
else
    echo -e "${GREEN}✓${NC} TA-Lib already installed"
fi

echo ""

# ==================== VERIFY INSTALLATION ====================

echo "🔍 Verifying installation..."
echo ""

# Check Docker is running
if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker daemon is running"
else
    echo -e "${RED}✗${NC} Docker daemon is not running"
    echo "Please start Docker and try again"
    exit 1
fi

# Check disk space
AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 10 ]; then
    echo -e "${YELLOW}!${NC} Low disk space: ${AVAILABLE_SPACE}GB available (10GB+ recommended)"
else
    echo -e "${GREEN}✓${NC} Sufficient disk space: ${AVAILABLE_SPACE}GB available"
fi

# Check memory
if [ "$OS" = "linux" ] || [ "$OS" = "macos" ]; then
    TOTAL_MEM=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || sysctl hw.memsize | awk '{print int($2/1073741824)}')
    if [ "$TOTAL_MEM" -lt 4 ]; then
        echo -e "${YELLOW}!${NC} Low memory: ${TOTAL_MEM}GB (4GB+ recommended)"
    else
        echo -e "${GREEN}✓${NC} Sufficient memory: ${TOTAL_MEM}GB"
    fi
fi

echo ""

# ==================== CREATE DIRECTORIES ====================

echo "📁 Creating necessary directories..."
echo ""

mkdir -p logs
mkdir -p backups
mkdir -p database/migrations
mkdir -p infrastructure/nginx/ssl
mkdir -p backend/bots/ml-learning-engine/models
mkdir -p backend/bots/ml-learning-engine/notebooks

# Create log directories for each bot
for bot in market-data-bot news-collector-bot technical-analysis-bot \
           sentiment-analysis-bot itc-analysis-bot signal-aggregator-bot \
           ml-learning-engine notification-bot feedback-processor-bot monitoring-bot; do
    mkdir -p "backend/bots/${bot}/logs"
done

print_status "Directories created"
echo ""

# ==================== SET PERMISSIONS ====================

echo "🔐 Setting permissions..."
echo ""

# Make scripts executable
chmod +x scripts/**/*.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

print_status "Permissions set"
echo ""

# ==================== FINAL CHECKS ====================

echo "✅ Installation complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Next steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Initialize databases:"
echo "   ./scripts/setup/init_databases.sh"
echo ""
echo "2. Generate environment files:"
echo "   ./scripts/setup/generate_env_files.sh"
echo ""
echo "3. Configure your .env file with API keys"
echo ""
echo "4. Start the system:"
echo "   docker-compose up -d"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
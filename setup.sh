#!/usr/bin/env bash
# ==============================================================================
# Ajiputra-Project MovieBox API - Automated Linux Server Setup & Deployment Script
# Powered & Engineered by Ajiputra-Project
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================="${NC}
echo -e "${GREEN}  Ajiputra-Project MovieBox API - Linux Installer ${NC}"
echo -e "${BLUE}=================================================="${NC}

# Helper for elevated commands
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo &> /dev/null; then
        SUDO="sudo"
    fi
fi

# 1. Detect Package Manager and Install System Requirements (Verbose mode)
echo -e "\n${YELLOW}[1/5] Checking & installing system tools (python3, pip, venv, curl)...${NC}"

MISSING_TOOLS=0
command -v python3 &> /dev/null || MISSING_TOOLS=1
command -v curl &> /dev/null || MISSING_TOOLS=1

if [ "$MISSING_TOOLS" -eq 1 ]; then
    echo -e "${YELLOW}Installing required system packages via package manager...${NC}"
    if command -v apt-get &> /dev/null; then
        $SUDO apt-get update && $SUDO apt-get install -y python3 python3-pip python3-venv curl ca-certificates
    elif command -v dnf &> /dev/null; then
        $SUDO dnf install -y python3 python3-pip curl ca-certificates
    elif command -v yum &> /dev/null; then
        $SUDO yum install -y python3 python3-pip curl ca-certificates
    elif command -v pacman &> /dev/null; then
        $SUDO pacman -Sy --noconfirm python python-pip curl ca-certificates
    fi
else
    echo -e "${GREEN}✓ Core system tools (python3, curl) are present.${NC}"
fi

# 2. Setup Python Virtual Environment
echo -e "\n${YELLOW}[2/5] Setting up Python virtual environment (venv)...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv || {
        echo -e "${YELLOW}python3-venv missing, installing via apt...${NC}"
        if command -v apt-get &> /dev/null; then
            $SUDO apt-get update && $SUDO apt-get install -y python3-venv
        fi
        python3 -m venv venv
    }
    echo -e "${GREEN}✓ Created virtual environment in ./venv${NC}"
else
    echo -e "${GREEN}✓ Existing virtual environment detected in ./venv${NC}"
fi

# Activate venv
source venv/bin/activate

# 3. Install Python Dependencies with Detailed Progress Logs
echo -e "\n${YELLOW}[3/5] Installing Python dependencies from requirements.txt...${NC}"
pip install --upgrade pip
echo -e "${BLUE}Running pip install -r requirements.txt:${NC}"
pip install -r requirements.txt

# 4. Verify Installed Packages
echo -e "\n${YELLOW}[4/5] Verifying installed packages...${NC}"
python3 -c "
import sys
packages = ['fastapi', 'uvicorn', 'httpx']
all_ok = True
for pkg in packages:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, '__version__', 'OK')
        print(f'  \033[0;32m✓ {pkg} {ver}\033[0m')
    except ImportError as e:
        print(f'  \033[0;31m✗ {pkg} FAILED: {e}\033[0m')
        all_ok = False
if not all_ok:
    sys.exit(1)
"

# 5. Create Production Start Helper Script
echo -e "\n${YELLOW}[5/5] Generating production helper script (start.sh)...${NC}"

cat << 'EOF' > start.sh
#!/usr/bin/env bash
# Production Start Script for Ajiputra-Project MovieBox API
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PORT="${PORT:-8000}"
echo "Starting Ajiputra-Project MovieBox API on port $PORT..."
exec python main.py
EOF

chmod +x start.sh

echo -e "\n${GREEN}================================================= ${NC}"
echo -e "${GREEN} 🎉 INSTALLATION & VERIFICATION COMPLETED!        ${NC}"
echo -e "${GREEN}================================================= ${NC}"
echo -e "To start the API server on your Linux Server:"
echo -e "  ${BLUE}./start.sh${NC}"
echo -e ""
echo -e "Or run via Docker:"
echo -e "  ${BLUE}docker compose up -d${NC}"
echo -e ""

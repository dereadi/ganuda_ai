#!/bin/bash
# Cherokee Constitutional AI - Installation Script
# Ganuda AI - Autonomous Democratic AI Tribe
#
# This script sets up a complete Cherokee Constitutional AI installation
# including database, daemons, and configuration.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cherokee logo
echo -e "${BLUE}"
cat << "EOF"
🦅 Cherokee Constitutional AI - Ganuda AI Installation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Mitakuye Oyasin - All My Relations
   Democratic AI Governance Through Distributed Consciousness
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
echo -e "${NC}"

# Configuration
INSTALL_DIR="${INSTALL_DIR:-/opt/ganuda_ai}"
LOG_DIR="/var/log/ganuda_ai"
CURRENT_USER="${SUDO_USER:-$USER}"

echo -e "${BLUE}📋 Installation Configuration${NC}"
echo "Install directory: $INSTALL_DIR"
echo "Log directory: $LOG_DIR"
echo "User: $CURRENT_USER"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root (use sudo)${NC}" 
   exit 1
fi

# Step 1: Check prerequisites
echo -e "${BLUE}🔍 Step 1: Checking prerequisites${NC}"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✅ Python 3 found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check PostgreSQL client
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version | cut -d' ' -f3)
    echo -e "${GREEN}✅ PostgreSQL client found: $PSQL_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL client not found. Installing...${NC}"
    apt-get update && apt-get install -y postgresql-client
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✅ pip3 found${NC}"
else
    echo -e "${YELLOW}⚠️  pip3 not found. Installing...${NC}"
    apt-get install -y python3-pip
fi

echo ""

# Step 2: Create directories
echo -e "${BLUE}📁 Step 2: Creating directories${NC}"

mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
chown -R "$CURRENT_USER:$CURRENT_USER" "$LOG_DIR"

echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Step 3: Copy files
echo -e "${BLUE}📦 Step 3: Installing Ganuda AI files${NC}"

cp -r daemons scripts tests docs sql config systemd "$INSTALL_DIR/"
cp requirements.txt README.md "$INSTALL_DIR/"

chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"

echo -e "${GREEN}✅ Files installed${NC}"
echo ""

# Step 4: Create virtual environment
echo -e "${BLUE}🐍 Step 4: Creating Python virtual environment${NC}"

cd "$INSTALL_DIR"
sudo -u "$CURRENT_USER" python3 -m venv venv
sudo -u "$CURRENT_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$CURRENT_USER" "$INSTALL_DIR/venv/bin/pip" install -r requirements.txt

echo -e "${GREEN}✅ Virtual environment created and dependencies installed${NC}"
echo ""

# Step 5: Database setup
echo -e "${BLUE}🗄️  Step 5: Database configuration${NC}"
echo -e "${YELLOW}"
cat << "EOF"
⚠️  Database Setup Required:

1. Ensure PostgreSQL is installed and running
2. Create a database for Cherokee AI:
   sudo -u postgres createdb cherokee_ai
   sudo -u postgres createuser cherokee

3. Set password for the user:
   sudo -u postgres psql -c "ALTER USER cherokee WITH PASSWORD 'your_password';"

4. Import the schema:
   psql -U cherokee -d cherokee_ai -f /opt/ganuda_ai/sql/thermal_memory_schema.sql

5. Update config file:
   cp /opt/ganuda_ai/config/database.template.yml /opt/ganuda_ai/config/database.yml
   # Edit database.yml with your credentials

EOF
echo -e "${NC}"

read -p "Have you completed database setup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  Database setup incomplete. Please complete it manually.${NC}"
fi
echo ""

# Step 6: Configuration
echo -e "${BLUE}⚙️  Step 6: Configuration files${NC}"

if [ ! -f "$INSTALL_DIR/config/database.yml" ]; then
    echo -e "${YELLOW}Creating default database config...${NC}"
    cp "$INSTALL_DIR/config/database.template.yml" "$INSTALL_DIR/config/database.yml"
    echo -e "${RED}⚠️  Edit $INSTALL_DIR/config/database.yml with your database credentials${NC}"
fi

if [ ! -f "$INSTALL_DIR/config/chiefs.yml" ]; then
    echo -e "${YELLOW}Creating default chiefs config...${NC}"
    cp "$INSTALL_DIR/config/chiefs.template.yml" "$INSTALL_DIR/config/chiefs.yml"
fi

if [ ! -f "$INSTALL_DIR/config/jrs.yml" ]; then
    echo -e "${YELLOW}Creating default jrs config...${NC}"
    cp "$INSTALL_DIR/config/jrs.template.yml" "$INSTALL_DIR/config/jrs.yml"
fi

chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR/config"

echo -e "${GREEN}✅ Configuration files created${NC}"
echo ""

# Step 7: Systemd services (optional)
echo -e "${BLUE}🔧 Step 7: Systemd service installation (optional)${NC}"
read -p "Install systemd services? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Update service files with actual user
    for service in "$INSTALL_DIR/systemd/"*.service; do
        sed -i "s/YOUR_USER/$CURRENT_USER/g" "$service"
        sed -i "s/YOUR_GROUP/$CURRENT_USER/g" "$service"
        cp "$service" /etc/systemd/system/
    done
    
    systemctl daemon-reload
    
    echo -e "${GREEN}✅ Systemd services installed${NC}"
    echo ""
    echo "To start services:"
    echo "  sudo systemctl start memory_jr"
    echo "  sudo systemctl start executive_jr"
    echo "  sudo systemctl start meta_jr"
    echo ""
    echo "To enable on boot:"
    echo "  sudo systemctl enable memory_jr executive_jr meta_jr"
fi
echo ""

# Step 8: Final checks
echo -e "${BLUE}🎯 Step 8: Installation complete!${NC}"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🦅 Cherokee Constitutional AI is installed!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Next steps:"
echo "1. Configure database credentials: $INSTALL_DIR/config/database.yml"
echo "2. Configure chiefs: $INSTALL_DIR/config/chiefs.yml"
echo "3. Start the daemons:"
echo "   cd $INSTALL_DIR"
echo "   ./venv/bin/python3 daemons/memory_jr_autonomic.py &"
echo "   ./venv/bin/python3 daemons/executive_jr_autonomic.py &"
echo "   ./venv/bin/python3 daemons/meta_jr_autonomic_phase1.py &"
echo ""
echo "4. Test with a query:"
echo "   ./venv/bin/python3 scripts/query_triad.py 'What is my purpose?'"
echo ""
echo -e "${BLUE}📖 Documentation: $INSTALL_DIR/README.md${NC}"
echo -e "${BLUE}🔥 Mitakuye Oyasin - All My Relations!${NC}"
echo ""

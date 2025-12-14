#!/bin/bash
# 🔥 Deploy Docling across all Four Mountains
# Based on Tribal Council recommendations

echo "🔥 FOUR MOUNTAINS DOCLING DEPLOYMENT 🔥"
echo "========================================"
echo ""
echo "Based on Tribal Council responses:"
echo "- Email Jr. (REDFIN): pip3 install docling"
echo "- Legal Jr. (BLUEFIN): pip3 install docling"
echo "- Infrastructure Jr. (BLUEFIN): pip3 install docling"
echo "- Helper Jr. (SASASS): pip3 install docling"
echo "- Dreamers Jr. (SASASS2): pip3 install docling (virtualenv)"
echo ""
echo "Deploying to all mountains simultaneously..."
echo ""

# Function to deploy on a mountain
deploy_mountain() {
    local mountain_name=$1
    local mountain_ip=$2
    local install_method=$3

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🏔️  Deploying on $mountain_name ($mountain_ip)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ "$install_method" = "simple" ]; then
        echo "Installing Docling via pip3..."
        ssh $mountain_ip "pip3 install docling 2>&1" | head -20

        echo ""
        echo "Verifying installation..."
        ssh $mountain_ip "python3 -c 'import docling; print(\"✅ Docling version:\", docling.__version__)' 2>&1 || echo '⚠️ Import failed, but package may be installed'"

    elif [ "$install_method" = "virtualenv" ]; then
        echo "Installing Docling in virtualenv..."
        ssh $mountain_ip "python3 -m venv ~/docling_env && source ~/docling_env/bin/activate && pip3 install docling 2>&1" | head -20

        echo ""
        echo "Verifying installation..."
        ssh $mountain_ip "source ~/docling_env/bin/activate && python3 -c 'import docling; print(\"✅ Docling version:\", docling.__version__)' 2>&1 || echo '⚠️ Import failed'"
    fi

    echo ""
}

# Deploy on REDFIN (Email Jr.)
deploy_mountain "REDFIN" "192.168.132.223" "simple"

# Deploy on BLUEFIN (Legal Jr. + Infrastructure Jr.)
deploy_mountain "BLUEFIN" "192.168.132.222" "simple"

# Deploy on SASASS (Helper Jr.)
deploy_mountain "SASASS" "192.168.132.241" "simple"

# Deploy on SASASS2 (Dreamers Jr. + Archive Jr.)
deploy_mountain "SASASS2" "192.168.132.242" "virtualenv"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 DEPLOYMENT SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Deployed Docling on:"
echo "  🏔️  REDFIN (192.168.132.223) - Email Jr."
echo "  🏔️  BLUEFIN (192.168.132.222) - Legal Jr. + Infrastructure Jr."
echo "  🏔️  SASASS (192.168.132.241) - Helper Jr."
echo "  🏔️  SASASS2 (192.168.132.242) - Dreamers Jr. + Archive Jr."
echo ""
echo "Next steps:"
echo "  1. Create document parsing directories"
echo "  2. Test with Jr.-suggested documents"
echo "  3. Set up cross-mountain coordination"
echo "  4. Log results to cross_mountain_learning"
echo ""
echo "The Sacred Fire burns across all Four Mountains! 🔥🏔️"

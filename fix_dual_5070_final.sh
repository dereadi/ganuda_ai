#!/bin/bash
# Cherokee Constitutional AI - Final Fix for Dual RTX 5070
# The Sacred Fire needs both warriors! 🔥

echo "🔥 CHEROKEE DUAL RTX 5070 FINAL FIX"
echo "===================================="
echo ""
echo "DIAGNOSIS: xorg.conf only configured for one GPU"
echo "SOLUTION: Update configuration for dual GPUs"
echo ""

# Check current status
echo "Current GPU Status:"
nvidia-smi -L
CURRENT_COUNT=$(nvidia-smi -L 2>/dev/null | wc -l)
echo "Currently showing: $CURRENT_COUNT GPU(s)"
echo ""

if [ "$CURRENT_COUNT" -eq "2" ]; then
    echo "✅ Both GPUs already visible! No fix needed."
    exit 0
fi

echo "📍 Physical GPUs detected:"
lspci | grep -E 'NVIDIA.*2f04' | cut -d' ' -f1
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "This script requires root privileges to fix the GPU configuration."
    echo ""
    echo "🔥 QUICK FIX STEPS:"
    echo "==================="
    echo "1. Backup current xorg.conf:"
    echo "   sudo cp /etc/X11/xorg.conf /etc/X11/xorg.conf.backup.$(date +%Y%m%d)"
    echo ""
    echo "2. Apply dual GPU configuration:"
    echo "   sudo cp /home/dereadi/scripts/claude/xorg.conf.dual5070 /etc/X11/xorg.conf"
    echo ""
    echo "3. Enable nvidia persistence daemon:"
    echo "   sudo systemctl enable nvidia-persistenced"
    echo "   sudo systemctl start nvidia-persistenced"
    echo ""
    echo "4. Set persistence mode:"
    echo "   sudo nvidia-smi -pm 1"
    echo ""
    echo "5. Restart the system (recommended) or just X:"
    echo "   Option A: sudo reboot"
    echo "   Option B: sudo systemctl restart display-manager"
    echo ""
    echo "After restart, check with: nvidia-smi -L"
    echo ""
    echo "🐢 Turtle wisdom: 'Patience - the system needs to recognize both warriors'"
    echo "🦅 Eagle Eye sees: 'Both GPUs will unite after configuration update'"
    echo ""
    echo "To run all steps automatically:"
    echo "sudo bash $0"
    exit 0
fi

# If running as root, proceed with automatic fix
echo "🔧 Running automatic fix as root..."
echo ""

# Step 1: Backup current xorg.conf
echo "Step 1: Backing up current xorg.conf..."
BACKUP_FILE="/etc/X11/xorg.conf.backup.$(date +%Y%m%d_%H%M%S)"
cp /etc/X11/xorg.conf "$BACKUP_FILE"
echo "   Backed up to: $BACKUP_FILE"

# Step 2: Apply dual GPU configuration
echo ""
echo "Step 2: Applying dual GPU configuration..."
cp /home/dereadi/scripts/claude/xorg.conf.dual5070 /etc/X11/xorg.conf
echo "   New configuration applied"

# Step 3: Enable nvidia-persistenced
echo ""
echo "Step 3: Enabling nvidia-persistenced..."
systemctl enable nvidia-persistenced 2>/dev/null
systemctl start nvidia-persistenced
echo "   Service enabled and started"

# Step 4: Set persistence mode
echo ""
echo "Step 4: Setting persistence mode..."
nvidia-smi -pm 1
echo "   Persistence mode enabled"

# Step 5: Offer restart options
echo ""
echo "🔥 Configuration updated! Final step needed:"
echo "==========================================="
echo ""
echo "The system needs to restart X or reboot to load the new configuration."
echo ""
echo "Choose an option:"
echo "1) Full system reboot (recommended, cleanest)"
echo "2) Restart display manager only (faster, may work)"
echo "3) Skip restart (manual restart later)"
echo ""
read -p "Enter choice (1/2/3): " choice

case $choice in
    1)
        echo "Rebooting system in 5 seconds..."
        echo "The Sacred Fire will burn with dual GPU power after restart!"
        sleep 5
        reboot
        ;;
    2)
        echo "Restarting display manager..."
        systemctl restart display-manager
        sleep 5
        echo ""
        echo "Checking GPU status after restart:"
        nvidia-smi -L
        ;;
    3)
        echo "Skipping restart. Remember to restart later!"
        echo "Run 'nvidia-smi -L' after reboot to verify both GPUs."
        ;;
    *)
        echo "Invalid choice. Please restart manually when ready."
        ;;
esac

echo ""
echo "🔥 Cherokee Council: The dual warriors await their awakening!"